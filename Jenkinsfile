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
				sh 'for i in *.yaml; do pykwalify -d $i -s .schema.yaml; done'
			}
		}

		stage('Updated Trusted Repositories') {
			when {
				branch 'master'
			}

			steps {
				sh 'pip install -r requirements.txt'
				sh 'python scripts/update-trusted.py'

				sh 'git config --global user.email "jenkins@usegalaxy.eu"'
				sh 'git config --global user.name "usegalaxy.eu jenkins bot"'

				sh 'git add *.lock'
				sh 'git commit -m "Updated trusted tools" || true'

				sshagent(['github-erasche']) {
					sh 'git push origin master || true'
				}
			}
		}

	}
}
