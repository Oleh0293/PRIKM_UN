pipeline {
    agent any

    environment {
        DOCKERHUB_USER = 'dante0293'
        IMAGE_NAME     = 'prikm'
        REGISTRY_IMAGE = "${DOCKERHUB_USER}/${IMAGE_NAME}"
    }

    stages {
        stage('Start') {
            steps {
                echo 'Lab_2: started by GitHub'
            }
        }

        stage('Image build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:latest ."
                sh "docker tag ${IMAGE_NAME} ${REGISTRY_IMAGE}:latest"
                sh "docker tag ${IMAGE_NAME} ${REGISTRY_IMAGE}:${BUILD_NUMBER}"
            }
        }

        stage('Push to registry') {
            steps {
                withDockerRegistry([ credentialsId: "dockerhub", url: "" ]) {
                    sh "docker push ${REGISTRY_IMAGE}:latest"
                    sh "docker push ${REGISTRY_IMAGE}:${BUILD_NUMBER}"
                }
            }
        }

        stage('Deploy image') {
            steps {
                sh 'docker stop prod_nginx 2>/dev/null || true'
                sh 'docker rm prod_nginx 2>/dev/null || true'
                sh 'docker ps -q --filter "publish=80" | xargs -r docker rm -f 2>/dev/null || true'
                sh "docker run -d --name prod_nginx -p 80:80 ${REGISTRY_IMAGE}:latest"
            }
        }
    }

    post {
        success {
            echo "Pipeline SUCCESS — ${REGISTRY_IMAGE}:${BUILD_NUMBER} deployed"
        }
        failure {
            echo 'Pipeline FAILED — check the logs above'
            sh 'docker stop prod_nginx 2>/dev/null || true'
            sh 'docker rm prod_nginx 2>/dev/null || true'
            sh 'docker ps -q --filter "publish=80" | xargs -r docker rm -f 2>/dev/null || true'
        }
    }
}
