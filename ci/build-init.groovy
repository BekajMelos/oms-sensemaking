#!groovy

pipeline {
    agent {
        label params.AGENT
    }

    parameters {
        string(
            name: 'AGENT',
            defaultValue: 'CODE',
            description: 'use a specific agent(s) by label to run the build on')
    }

    environment {
        SERVICE_ACCOUNT_ID = 'art-svc-aio4-dev-dev'
        SERVICE_ACCOUNT = credentials("${SERVICE_ACCOUNT_ID}")

        SONARQUBE_URL = 'https://sonarqube.code.dodiis.mil/'
        SONARQUBE_API_KEY = credentials('sonar-svc-aio4-dev')
        SONARQUBE_PROJECT = 'aio4-dev:oms-sensemaking'
    }

    stages {
        stage('Prepare') {
            agent {
                dockerfile {
                    label params.AGENT
                    filename 'ci/Dockerfile.jenkins'
                    registryUrl 'https://${artDockerUrl}'
                    registryCredentialsId env.SERVICE_ACCOUNT_ID
                    additionalBuildArgs '--build-arg BASE_IMAGE=${artDockerUrl}/python:3.10.14-slim'
                    args '-e HOME=/tmp'
                }
            }
            stages {
                stage('Install') {
                    steps {
                        sh '''
                            python -m venv /tmp/venv
                            . /tmp/venv/bin/activate

                            pip install poetry
                            poetry install --all-extras
                        '''
                    }
                }
                stage('Test') {
                    steps {
                        sh '''
                            . /tmp/venv/bin/activate
                            set -a
                            . ci/aide.env
                            set +a

                            poetry run python -m pytest tests --cov-report=xml || true
                        '''
                        stash(includes: 'coverage.xml', name: 'coverage')
                    }
                }
                stage('Build') {
                    steps {
                        sh '''
                            . /tmp/venv/bin/activate

                            poetry self add poetry-dynamic-versioning
                            poetry build
                        '''
                        stash(includes: 'dist/*.whl', name: 'packages')
                    }
                    post {
                        always {
                            archiveArtifacts(
                                artifacts: 'dist/*.whl',
                                onlyIfSuccessful: false)
                        }
                    }

                }
            }
        }
        stage('Publish') {
            steps {
                unstash('packages')
                script {
                    def server = Artifactory.newServer(
                        url: env.artUrl,
                        credentialsId: env.SERVICE_ACCOUNT_ID
                    )

                    def uploadSpec = '''
                        {
                            "files": [
                                {
                                    "pattern": "dist/oms*.whl",
                                    "target": "pypi-proj-local/aio4/dev/services/oms/"
                                }
                            ]
                        }
                    '''

                    def buildInfo = server.upload(spec: uploadSpec)
                    server.publishBuildInfo(buildInfo)
                }
            }
        }
        stage('Scan') {
            steps {
                unstash('coverage')
                sh '''
                    /jenkins2/dependency-check/bin/dependency-check.sh -n -s . \
                        --disableOssIndex \
                        --enableExperimental \
                        --project ${SONARQUBE_PROJECT/:/-} \
                        -f ALL
                    /jenkins2/sonar-scanner/bin/sonar-scanner \
                        -Dsonar.host.url=${SONARQUBE_URL} \
                        -Dsonar.login=${SONARQUBE_API_KEY} \
                        -Dsonar.projectKey=${SONARQUBE_PROJECT} \
                        -Dsonar.sources=oms_sdk \
                        -Dsonar.dependencyCheck.htmlReportPath=dependency-check-report.html \
                        -Dsonar.python.coverage.reportPaths=coverage.xml
                '''
            }
            post {
                always {
                    archiveArtifacts(
                        artifacts: '*.html',
                        allowEmptyArchive: true,
                        onlyIfSuccessful: false
                    )
                }
            }
        }
    }

    post {
        always {
            cleanWs(disableDeferredWipeout: true)
        }
    }
}
