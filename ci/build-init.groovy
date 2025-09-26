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
        booleanParam(
            name: 'SKIP_UNIT_TESTS',
            defaultValue: true,
            description: 'whether or not to skip unit tests')
    }

    environment {
        SERVICE_ACCOUNT_ID = 'art-svc-aio4-sirius-dev'
        SERVICE_ACCOUNT = credentials("${SERVICE_ACCOUNT_ID}")

        SONARQUBE_URL = 'https://sonarqube.code.dodiis.mil/'
        SONARQUBE_API_KEY = credentials('sonar-svc-aio4-dev')
        SONARQUBE_PROJECT = 'aio4-dev:oms-sensemaking'

        PYTHON_VERSION = sh(script: 'cat .python-version', returnStdout: true).trim()

        DOCKER_PROD_IMAGE = 'aio4/dev/services/oms/oms-sensemaking'

        IMAGE_NAME="dpaas/ubi8-ccp"
        IMAGE_VERSION="8.10"

        POSTGRES_REPOSITORY = "https://artifactory.code.dodiis.mil/artifactory/postgres-remote"
        EPEL_REPOSITORY = "https://artifactory.code.dodiis.mil/artifactory/epel-remote"

        APP_VERSION = "${env.TAG_NAME ? env.TAG_NAME : 'latest'}"
    }

    stages {
        stage('Prepare') {
            agent {
                dockerfile {
                    label params.AGENT
                    filename 'ci/Dockerfile.jenkins'
                    registryUrl 'https://${artDockerUrl}'
                    registryCredentialsId env.SERVICE_ACCOUNT_ID
                    additionalBuildArgs '--build-arg BASE_IMAGE=${artDockerUrl}/${IMAGE_NAME}:${IMAGE_VERSION}'
                    args '''
                        -e HOME=/tmp \
                        -v /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem:/etc/ssl/certs/ca-certificates.crt
                    '''
                }
            }
            stages {
                stage('Version') {
                    steps {
                        sh '''
                            python -m venv /tmp/venv
                            . /tmp/venv/bin/activate

                            echo "machine artifactory.code.dodiis.mil" > ${HOME}/.netrc
                            echo "login ${SERVICE_ACCOUNT_USR}" >> ${HOME}/.netrc
                            echo "password ${SERVICE_ACCOUNT_PSW}" >> ${HOME}/.netrc

                            echo "[global]" > /tmp/venv/pip.conf
                            echo "index-url = ${artUrl}/api/pypi/pypi/simple" >> /tmp/venv/pip.conf
                            echo "trusted-host = artifactory.code.dodiis.mil" >> /tmp/venv/pip.conf

                            pip install -U pip wheel setuptools_scm
                        '''
                    }
                }
                stage('Install') {
                    when {
                        expression { params.SKIP_UNIT_TESTS == false }
                    }
                    steps {
                        sh '''
                            . /tmp/venv/bin/activate
                            pip install -e ".[dev,docs,test,build]"
                        '''
                    }
                }
                stage('Test') {
                    when {
                        expression { params.SKIP_UNIT_TESTS == false }
                    }
                    steps {
                        sh '''
                            . /tmp/venv/bin/activate
                            python -m pytest tests --cov-report=xml || true
                        '''
                        stash(includes: 'coverage.xml', name: 'coverage')
                    }
                }
            }
        }
        stage('Build') {
            steps {
                script {
                    docker.withRegistry('https://${artDockerUrl}', env.SERVICE_ACCOUNT_ID) {
                        sh '''
                            echo "machine artifactory.code.dodiis.mil" > .netrc
                            echo "login ${SERVICE_ACCOUNT_USR}" >> .netrc
                            echo "password ${SERVICE_ACCOUNT_PSW}" >> .netrc

                            docker build \
                                -t ${artDockerUrl}/${DOCKER_PROD_IMAGE}:${APP_VERSION%%+*} \
                                -t ${artDockerUrl}/${DOCKER_PROD_IMAGE}:latest \
                                --build-arg NAMESPACE=${artDockerUrl} \
                                --build-arg IMAGE_NAME=${IMAGE_NAME} \
                                --build-arg IMAGE_VERSION=${IMAGE_VERSION} \
                                --build-arg APP_VERSION=${APP_VERSION} \
                                --build-arg APP_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
                                --build-arg VCS_REF=$(git rev-parse HEAD) \
                                --build-arg PIP_INDEX_URL=${artUrl}/api/pypi/pypi/simple \
                                --build-arg POSTGRES_REPOSITORY=${POSTGRES_REPOSITORY} \
                                --build-arg EPEL_REPOSITORY=${EPEL_REPOSITORY} \
                                --secret id=mynetrc,src=.netrc \
                                --secret id=cacert,src=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem \
                                .
                            docker push --all-tags ${artDockerUrl}/${DOCKER_PROD_IMAGE}
                        '''
                    }
                }
            }
        }
        stage('Scan with Prisma') {
            steps {
                prismaCloudScanImage(
                    ca: '',
                    cert: '',
                    dockerAddress: 'unix:///var/run/docker.sock',
                    image: "${artDockerUrl}/${DOCKER_PROD_IMAGE}:${APP_VERSION}",
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
                script {
                    try {
                        unstash('coverage')
                    } catch (e) {
                        print 'failed to unstash coverage report. continuing...'
                    }
                }
                sh '''
                    touch coverage.xml
                    /jenkins2/dependency-check/bin/dependency-check.sh -n -s . \
                        --disableOssIndex \
                        --enableExperimental \
                        --project ${SONARQUBE_PROJECT/:/-} \
                        -f ALL
                    /jenkins2/sonar-scanner/bin/sonar-scanner \
                        -Dsonar.host.url=${SONARQUBE_URL} \
                        -Dsonar.login=${SONARQUBE_API_KEY} \
                        -Dsonar.projectKey=${SONARQUBE_PROJECT} \
                        -Dsonar.projectVersion=${APP_VERSION} \
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
            sh '''
                docker rmi ${artDockerUrl}/${DOCKER_PROD_IMAGE}:${APP_VERSION%%+*} || true
                docker rmi ${artDockerUrl}/${DOCKER_PROD_IMAGE}:latest || true
            '''
        }
    }
}
