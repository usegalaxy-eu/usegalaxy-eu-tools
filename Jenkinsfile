pipeline {
  agent any
  stages {
    stage('Linting') {
      steps {
        sh '''
        pip install --user -U -r requirements.txt
        '''
        sh '''
        for file in *.yaml; do
            python -c 'import sys; import yaml; import json; sys.stdout.write(json.dumps(yaml.load(sys.stdin), indent=2))' < $file;
        done;
        for file in *.yaml.lock; do
            python -c 'import sys; import yaml; import json; sys.stdout.write(json.dumps(yaml.load(sys.stdin), indent=2))' < $file;
        done;
        '''
      }
    }
    stage('Updated Trusted Repositories') {
      steps {
        sh '''
        git checkout master
        '''

        sh '''
        pip install --user -U -r requirements.txt
        '''
        sh '''
        python scripts/update-trusted.py
        '''

        sshagent(['501e17be-bcda-4159-8cc3-eae39c4797f5']) {
            sh 'git add *.lock'
            sh 'git config --global user.email "jenkins@usegalaxy.eu"'
            sh 'git config --global user.name "usegalaxy.eu jenkins bot"'
            sh 'git commit -m "Updated trusted tools" ||  true'
            sh 'git push origin master || true'
        }
      }
    }
  }
}
