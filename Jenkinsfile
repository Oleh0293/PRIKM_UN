pipeline {
    agent any

    triggers {
        cron('H/5 * * * *')
    }

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['dev', 'staging', 'prod'],
            description: 'Target deployment environment'
        )
        booleanParam(
            name: 'SKIP_PUSH',
            defaultValue: false,
            description: 'Skip pushing image to Docker Hub'
        )
        string(
            name: 'CUSTOM_TAG',
            defaultValue: '',
            description: 'Custom image tag (leave empty to use BUILD_NUMBER)'
        )
    }

    environment {
        DOCKERHUB_USER = 'dante0293'
        IMAGE_NAME     = 'prikm'
        REGISTRY_IMAGE = "${DOCKERHUB_USER}/${IMAGE_NAME}"
        IMAGE_TAG      = "${params.CUSTOM_TAG ?: env.BUILD_NUMBER}"
    }

    options {
        timestamps()
        office365ConnectorWebhooks([[
            name: 'Teams-O365',
            url: 'https://prod-33.westus2.logic.azure.com:443/workflows/0858bd9c584848e49aed11d9171438a1/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=sHQ961yQz5yL14j-vTz_hA4v24X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm4X7dC4xWm',
            startNotification: false,
            notifySuccess: true,
            notifyAborted: false,
            notifyNotBuilt: false,
            notifyUnstable: true,
            notifyFailure: true,
            notifyBackToNormal: true,
            notifyRepeatedFailure: false,
            timeout: 30000
        ]])
    }

    stages {
        stage('Start') {
            steps {
                echo "Lab_3: Pipeline #${BUILD_NUMBER}"
                echo "Environment: ${params.DEPLOY_ENV}"
                echo "Image tag:   ${IMAGE_TAG}"
                echo "Skip push:   ${params.SKIP_PUSH}"
                script {
                    currentBuild.displayName = "#${BUILD_NUMBER} [${params.DEPLOY_ENV}] ${IMAGE_TAG}"
                }
            }
        }

        stage('Build') {
            steps {
                echo "Building ${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY_IMAGE}:latest"
                sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY_IMAGE}:${IMAGE_TAG}"
            }
        }

        stage('Test') {
            steps {
                echo 'Running container health check...'
                sh "docker run --rm -d --name test_nginx -p 8888:80 ${IMAGE_NAME}:${IMAGE_TAG}"
                sh 'sleep 3'
                sh 'curl -f http://localhost:8888 || (docker stop test_nginx && exit 1)'
                sh 'docker stop test_nginx'
                echo 'Health check passed'
            }
        }

        stage('Push to registry') {
            when {
                expression { return !params.SKIP_PUSH }
            }
            steps {
                withDockerRegistry([ credentialsId: "1", url: "" ]) {
                    sh "docker push ${REGISTRY_IMAGE}:latest"
                    sh "docker push ${REGISTRY_IMAGE}:${IMAGE_TAG}"
                }
            }
        }

        stage('Deploy') {
            steps {
                sh 'docker stop prod_nginx 2>/dev/null || true'
                sh 'docker rm prod_nginx 2>/dev/null || true'
                sh 'docker ps -q --filter "publish=80" | xargs -r docker rm -f 2>/dev/null || true'
                sh "docker run -d --name prod_nginx -p 80:80 ${REGISTRY_IMAGE}:latest"
            }
        }

        stage('Report') {
            steps {
                script {
                    def reportDir = 'build-report'
                    sh "mkdir -p ${reportDir}"
                    writeFile file: "${reportDir}/index.html", text: """
                        <!doctype html>
                        <html><head><meta charset='utf-8'><title>Build Report #${BUILD_NUMBER}</title>
                        <style>
                            body { font-family: system-ui; background: #1a1a2e; color: #e0e0e0; padding: 40px; }
                            .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                                    border-radius: 16px; padding: 32px; max-width: 500px; margin: auto; }
                            h2 { color: #64b5f6; margin-bottom: 16px; }
                            table { width: 100%; border-collapse: collapse; }
                            td { padding: 8px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); }
                            td:first-child { color: #888; }
                            .ok { color: #81c784; font-weight: bold; }
                        </style></head><body><div class='card'>
                        <h2>Build Report #${BUILD_NUMBER}</h2>
                        <table>
                            <tr><td>Image</td><td>${REGISTRY_IMAGE}:${IMAGE_TAG}</td></tr>
                            <tr><td>Environment</td><td>${params.DEPLOY_ENV}</td></tr>
                            <tr><td>Push skipped</td><td>${params.SKIP_PUSH}</td></tr>
                            <tr><td>Branch</td><td>${env.GIT_BRANCH ?: 'Lab_2'}</td></tr>
                            <tr><td>Status</td><td class='ok'>SUCCESS</td></tr>
                        </table></div></body></html>
                    """
                    publishHTML(target: [
                        reportName: 'Build Report',
                        reportDir: reportDir,
                        reportFiles: 'index.html',
                        keepAll: true,
                        alwaysLinkToLastBuild: true,
                        allowMissing: false
                    ])
                    addBadge(icon: 'completed.gif', text: "${params.DEPLOY_ENV} - ${IMAGE_TAG}")
                    addShortText(text: "${params.DEPLOY_ENV}", background: '#4caf50', color: '#fff', border: 0)
                }
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCESS — ${REGISTRY_IMAGE}:${IMAGE_TAG} deployed to ${params.DEPLOY_ENV}"
        }
        failure {
            echo 'Pipeline FAILED — check the logs above'
            sh 'docker stop prod_nginx 2>/dev/null || true'
            sh 'docker rm prod_nginx 2>/dev/null || true'
            sh 'docker ps -q --filter "publish=80" | xargs -r docker rm -f 2>/dev/null || true'
        }
    }
}
