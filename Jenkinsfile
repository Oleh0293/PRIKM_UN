pipeline {
    agent any

    environment {
        IMAGE_NAME = 'nginx/custom'
        IMAGE_TAG  = 'latest'
        APP_PORT   = '80'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Branch: ${env.BRANCH_NAME ?: 'Lab_1'}"
                echo "Build:  #${env.BUILD_NUMBER}"
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo "Building ${IMAGE_NAME}:${IMAGE_TAG}"
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
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

        stage('Cleanup') {
            steps {
                echo 'Stopping previous deployment if exists...'
                sh 'docker stop prod_nginx 2>/dev/null || true'
                sh 'docker rm prod_nginx 2>/dev/null || true'
            }
        }

        stage('Deploy') {
            steps {
                echo "Deploying ${IMAGE_NAME}:${IMAGE_TAG} on port ${APP_PORT}"
                sh "docker run -d --name prod_nginx -p ${APP_PORT}:80 ${IMAGE_NAME}:${IMAGE_TAG}"
            }
        }

        stage('Verify') {
            steps {
                echo 'Verifying deployment...'
                sh 'sleep 3'
                sh "curl -f http://localhost:${APP_PORT}"
                echo 'Deployment verified — site is live!'
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCESS — ${IMAGE_NAME}:${IMAGE_TAG} is running on port ${APP_PORT}"
        }
        failure {
            echo 'Pipeline FAILED — check the logs above'
            sh 'docker stop prod_nginx 2>/dev/null || true'
            sh 'docker rm prod_nginx 2>/dev/null || true'
        }
    }
}
