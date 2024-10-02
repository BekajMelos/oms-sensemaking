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

        PYTHON_VERSION = sh(script: 'cat .python-version', returnStdout: true).trim()

        DOCKER_PROD_IMAGE = 'aio4/services/oms/oms-sensemaking:'
    }

    stages {
        stage('Prepare') {
            agent {
                dockerfile {
                    label params.AGENT
                    filename 'ci/Dockerfile.jenkins'
                    registryUrl 'https://${artDockerUrl}'
                    registryCredentialsId env.SERVICE_ACCOUNT_ID
                    additionalBuildArgs '--build-arg BASE_IMAGE=${artDockerUrl}/python:${PYTHON_VERSION}-slim'
                    args '''
                        -e HOME=/tmp \
                        -v /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/etc/ssl/certs/ca-certificates.crt
                    '''
                }
            }
            stages {
                stage('Install') {
                    steps {
                        sh '''
                            python -m venv /tmp/venv
                            . /tmp/venv/bin/activate
                            pip install -U pip wheel

                            echo "machine artifactory.code.dodiis.mil" > ${HOME}/.netrc
                            echo "login ${SERVICE_ACCOUNT_USR}" >> ${HOME}/.netrc
                            echo "password ${SERVICE_ACCOUNT_PSW}" >> ${HOME}/.netrc

                            echo "[global]" > /tmp/venv/pip.conf
                            echo "index-url = ${artUrl}/api/pypi/pypi" >> /tmp/venv/pip.conf
                            echo "extra-index-url = https://pypi.org/simple" >> /tmp/venv/pip.conf

                            pip install -e ".[dev,docs,test,build]"
                        '''

                        script {
                            env.APP_VERSION = sh(script: 'python -m setuptools_scm', returnStdout: true).trim()
                        }
                    }
                }
                stage('Test') {
                    steps {
                        sh '''
                            . /tmp/venv/bin/activate
                            set -a
                            . ci/aide.env
                            set +a

                            python -m pytest tests --cov-report=xml || true
                        '''
                        stash(includes: 'coverage.xml', name: 'coverage')
                    }
                }
            }
        }
        stage('Build') {
            steps {
                sh '''
                    . /tmp/venv/bin/activate

                    docker build \
                        -t ${artDockerUrl}/${DOCKER_PROD_IMAGE} \
                        --build-arg APP_VERSION=${APP_VERSION} \
                        --build-arg APP_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                        --build-arg VCS_REF=$(git rev-parse HEAD) \
                        --secret id=mynetrc,src=${HOME}/.netrc \
                        .
                    docker push ${artDockerUrl}/${DOCKER_PROD_IMAGE}
                '''
            }
        }
        stage('Scan with Prisma') {
            steps {
                prismaCloudScanImage(
                    ca: '',
                    cert: '',
                    dockerAddress: 'unix:///var/run/docker.sock',
                    image: "${artDockerUrl}/${DOCKER_PROD_IMAGE}",
                    key: '',
                    logLevel: 'info',
                    podmanPath: '',
                    project: '',
                    resultsFile: 'oms-sensemaking-prisma-scan.json',
                    ignoreImageBuildTime: true
                )
                prismaCloudPublish(
                    resultsFilePattern: 'oms-sensemaking-prisma-scan.json'
                )
            }
        }
        stage('Scan with SonarQube') {
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
                        -Dsonar.sources=src \
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
