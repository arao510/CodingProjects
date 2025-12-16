1.1 Name should reveal purpose
    - descriptive name that explains why something exists 
    - ex: ip_address = get_ip_address(packet)

1.2 Function should only do 1 thing and only 1 thing
    - ex: convert_to_timestamp(time)

1.3 Reduce duplication
    - if duplication is present, practice abstraction 

1.4 Organize files consistently
    - Create folders if you need but organize files for consistency 
    - ex: all simulation attacks should be in the tools directory

1.5 Keeps compilers clean 
    - No errors should be popping up in compilers when running application

1.6 One purpose per route
    - Each api endpoint should only do what it is programmed to do 
    - ex: ssh_baseline endpoint should only push baseline metrics for ssh

1.7 Stay consistent with variable names
    - Really would appreciate use of camel cases just so all variable name stay consistent

1.8 One empty line between each function
    - This is strictly so it's easier to read 