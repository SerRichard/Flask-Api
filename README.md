# **Flask Api for c02-Intensity**

With user registration, token authentication, and microservicing

**note:** This API will only recieve the first segment of a UK standard postcode.
For example. E1 3BB, only E1, drop the second segment.

## Installation and preparation: Linux users

Prepare your working environment
```
sudo apt update
sudo apt install python3-pip
sudo apt install docker.io
sudo mkdir c02-app
cd c02-app
```

Get the info from the repository
```
sudo wget -O requirements.txt https://raw.githubusercontent.com/SerRichard/Flask-Api/master/requirements.txt
sudo wget -O Dockerfile https://raw.githubusercontent.com/SerRichard/Flask-Api/master/Dockerfile
sudo wget -O c02_api.py https://raw.githubusercontent.com/SerRichard/Flask-Api/master/c02_api.py
sudo wget -O c02.csv https://raw.githubusercontent.com/SerRichard/Flask-Api/master/c02.csv
```

Then set up your CQL database
```
sudo docker pull cassandra:latest
sudo docker run --name c02-docker -p 9042:9042 -d cassandra:latest
sudo docker cp c02.csv c02-docker:/home/c02.csv
```

After setting up the cassanda docker, go ahead and run the database
```
sudo docker exec -it c02-docker cqlsh
```

Now create the keyspace and table to store the API's data
```
CREATE KEYSPACE c02 WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor' : 1};
CREATE TABLE c02.stats (postcode text PRIMARY KEY, name text, regionid int, forecast text, indx text, Date text);
COPY c02.stats(postcode,name,regionid,forecast,indx,date) FROM '/home/c02.csv' WITH DELIMITER=',' AND HEADER=True;
QUIT
```

Returning to terminal, it is important to ensure the python code will try to connect to the correct location.
Open the c02_api.py
```
sudo nano c02_api.py
```

Modify the IP address in the following line, to your own IP address.
```
cluster = Cluster(contact_points=['54.167.248.218'],port=9042)
```
*Ctrl+C and save changes*

Now we have the requirements installed and the database set up, the server is ready to run

## Running (directly or via docker)

Run from file.
```
sudo pip3 install -r requirements.txt
sudo python3 c02_api.py
```

Or set up a docker, and run the server via docker.
```
sudo docker build . --tag=c02_api:v1
sudo docker run -p 80:80 c02_api:v1
```

Now the server is running. Requests can be sent from a different window.

## API Documentation

**POST** /register 

Register a new user.
The request must contain a JSON object that defines username and password.
If succesful, a 201 is returned along with the new user's username.
If unsuccessful, a 400 will be returned for either no username or password value
being submitted, or if the username already exists.

Example register:
```
curl -i -H "Content-Type: application/json" -X POST -d '{"username":"foxie","password":"banana"}' ec2-35-171-189-126.compute-1.amazonaws.com/register
```

**GET** /user

Find out if a user is registered.
If successful, returns 200. If username field empty, or username does not exist, 400.

Example register:
```
curl -i -H "Content-Type: application/json" -X GET -d '{"username":"foxie"}' ec2-35-171-189-126.compute-1.amazonaws.com/user
```

**GET** /token

Use user information to get a token for accession protected app.route's.
The request must contain the username and password.
If unsuccessful, a 400 will be returned on default.
If successful, 200 is returned along with the generated token.
This token is unique and will be valid for a 30 minute period. Must be
supplied when accessing protect routes.

Example get token:
```
curl -u foxie:banana -i -X GET ec2-35-171-189-126.compute-1.amazonaws.com/token
```

**GET (internal)** /c02/postcodes

Get data entries. 200 if successful. 404 if bad postcode given.
This request will pull all of the enteries for different postcodes that are in the API database,
and return them.

Example internal get:
```
curl -i ec2-35-171-189-126.compute-1.amazonaws.com/c02/postcodes
```

**GET (internal)** /c02/**postcode**

Get data entries. 200 if successful. 404 if bad postcode given.
This request will pull all of the enteries for one specific postcode that is in the API database,
and return them.

Example internal a specific get:
```
curl -i ec2-35-171-189-126.compute-1.amazonaws.com/c02/E1
```

**GET (external)** /new/**postcode**

Submit a curl GET request and the route shall be the first section of a standard UK postcode.
This request tells the API to access an external API and get latest c02 intestity for the postcode.
If sucessful, a 200 is returned with the data from the external API.
404 if bad postcode given.

Example external get:
```
curl -i ec2-35-171-189-126.compute-1.amazonaws.com/new/E1
```

**POST** /c02/postcode

Post a new postcode. Protected with authentication. Requires token.
This request posts a new entry to the API, and commits it to the database.
This will return a 201 for successful requests.
404 if bad postcode given.

Example post entry:
```
curl -i -H "Content-Type:application/json" -X POST -d '{"regionid":13,"name":"South East","postcode":"ME16","forecast":"215","indx":"moderate","date":"24-03-2020"}' --user _insert token here_:x c2-35-171-189-126.compute-1.amazonaws.com/c02/postcode
```

**PUT** /c02/postcode

Update a postcode entry in the database. Protected with authentication. Requires token.
This request allows the user to update an entry in API. Update forecast, indx and date.
Successful put returns 200. 404 if bad postcode given.

Example put (update) entry:
```
curl -i -H "Content-Type:application/json" -X PUT -d '{"postcode":"ME16","forecast":"458","indx":"High","date":"10-04-2020"}' --user _insert token here_:x  c2-35-171-189-126.compute-1.amazonaws.com/c02/postcode
```

**DELETE** /c02/postcode

Remove a postcode entry from the database. This may be done if duplicate entries are found.
This request is protected with authenticion and requires a token. Only takes one entry
(the postcode) in the JSON object. Returning a 200 on success. 404 if bad postcode given.

Example delete entry:
```
curl -i -H "Content-Type:application/json" -X DELETE -d '{"postcode":"E1"}' --user _insert token here_:x  c2-35-171-189-126.compute-1.amazonaws.com/c02/postcode
```
