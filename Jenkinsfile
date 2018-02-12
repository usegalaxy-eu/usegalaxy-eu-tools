pipeline {
	agent {
		docker {
			image 'python:2.7'
			args '-u root'
		}
	}

	stages {

		stage('Linting') {
			steps {
				sh 'pip install -r requirements.txt'
				sh 'make lint'
			}
		}

		stage('Updated Trusted Repositories') {
			when {
				branch 'master'
			}

			steps {
				sh 'pip install -r requirements.txt'
				sh 'make update_trusted'

				sh 'mkdir -p ~/.ssh'
				sh 'ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts'

				sshagent(['21341801-8530-459e-bed7-40057c7b98ff']) {
					sh 'git push git@github.com:usegalaxy-eu/usegalaxy-eu-tools.git master'
				}
			}
		}

	}
}
