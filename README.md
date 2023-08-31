# App_FlaskAPIMongo

Flask application with an API interface which talks with MongoDB

# Description

-   Flask application to provide MongoDB API
-   Provides middleware connection between MongoDB backend and Single Page Application (SPA) or moble frontend
-   Configuration is loaded from a local file
-   Events are logged

# ToDo's

-   Build application - STARTED

# Development Startup

0.  For each option, first do this:

    ```
    cd [parent folder you want to install under]
    git clone https://github.com/DykemaBill/App_FlaskAPIMongo.git
    cd App_FlaskAPIMongo
    pipenv shell
    pip3 install -r requirements.txt
    ```

1.  Flask standard option number 1:

    ```
    flask run
    ```

2.  Flask standard option number 2:

    ```
    python app_fam.py
    ```

2.  Wrapper that NGINX/uWSGI will use if you follow the above install:

    ```
    python wsgi.py
    ```

# Production Install and Setup (Linux)

1.  Python / Git
    1.  Install Python 3.8 or newer if not already installed
        1.  You will need to modify the repo ```Pipfile``` to match your installed version after your clone it
    2.  Install Python pipenv:

        ```
        pip3 install pipenv
        ```

    3.  Install the latest version of Git if not already installed
2.  uWSGI
    1.  Add an account to the system for this application to run under
        1.  Recommend creating a user called ```flask``` and using an existing group such as ```www-data```
    2.  Create a folder where uWSGI can send logs:

        ```
        mkdir /var/log/uwsgi
        chown -R flask:www-data /var/log/uwsgi
        ```

        1.  If you use a different log location, you will need to modify the repo ```wsgi.ini``` file
    3.  Install uWSGI:

        ```
        pip3 install uwsgi
        ```

3.  Flask application
    1.  Install this application on an external (non-root) filesystem:

        ```
        mkdir /[mountpath]/app
        cd /[mountpath]/app
        git clone https://github.com/DykemaBill/App_FlaskAPIMongo.git
        chown -R flask:www-data /[mountpath]/app/App_FlaskAPIMongo
        su - flask
        cd /[mountpath]/app/App_FlaskAPIMongo
        pipenv shell
        pip3 install -r requirements.txt
        deactivate
        exit
        ```

    2.  Setup a service (showing configuration for Ubuntu)
        1.  Create a configuration file

            ```
            touch /etc/systemd/system/App_FlaskAPIMongo.service
            ```

        2.  Put the following in this file (replace mountpath and mypipenvlocation)

            ```
            [Unit]
            Description=uWSGI instance to serve App_FlaskAPIMongo
            After=network.target

            [Service]
            User=flask
            Group=www-data
            WorkingDirectory=/mountpath/app/App_FlaskAPIMongo
            Environment="PATH=/var/app/.local/share/virtualenvs/mypipenvlocation/bin"
            ExecStart=/var/app/.local/share/virtualenvs/mypipenvlocation/bin/uwsgi --ini wsgi.ini

            [Install]
            WantedBy=multi-user.target
            ```

4.  NGINX
    1.  Setup a site
        1.  Create a configuration file

            ```
            touch /etc/nginx/sites-available/App_FlaskAPIMongo
            ln -s /etc/nginx/sites-available/App_FlaskAPIMongo /etc/nginx/sites-enabled
            ```

        2.  Put the following in this file (replace myservername.mytld, cert file locations and mountpath)

            ```
            server {
                listen 80;
                server_name flask.myservername.mytld;
                return 301 https://$server_name$request_uri;
            }

            server {
                listen 443 ssl;
                server_name flask.myservername.mytld;

                ssl_certificate /sslcertlocation/certfile.crt; 
                ssl_certificate_key /sslcertlocation/certkey.key;

                location / {
                    include uwsgi_params;
                    uwsgi_pass unix:/mountpath/app/App_FlaskAPIMongo/wsgi.sock;
                }
            }
            ```

    2.  Set NGINX and Flask startup to be active (showing configuration for Ubuntu)

        ```
        systemctl start App_FlaskAPIMongo
        systemctl enable App_FlaskAPIMongo
        systemctl status App_FlaskAPIMongo
        nginx -t
        systemctl restart nginx
        ufw allow 'Nginx Full'
        ```
