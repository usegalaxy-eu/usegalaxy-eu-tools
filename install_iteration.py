import sys
from subprocess import check_output

tools_file=sys.argv[1]
server_url=sys.argv[2]
api_key=sys.argv[3]

connection_fail=True
install_commands=['shed-tools','install','-t',tools_file,'-g',server_url,'-a',api_key]

while connection_fail:
    try:
        output = check_output(install_commands)
        connection_fail=False
    except Exception, e:
        #something happened, just print the msg and ignore 
        print(str(e.output))
