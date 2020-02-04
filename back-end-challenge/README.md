# Penn Club Review

Penn Club Review is both a REST API and a front-end interface that allows users to interact with Penn Clubs data

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the necessary packages

## Usage

Use Postman or the terminal to make get/post requests to the API portion. Make sure that they are in JSON format. 

For the /api/clubs post route, ensure that the JSON request has the "club_name" "tags" and "description" keys
For the /api/clubs put route, ensure that the JSON request has the "original_name" "new_name" "new_tags and "new_desc" keys
For the /api/favorite post route, ensure that the JSON request has the "username" and "club_name" tags

Sample user has username and password as "jen"

## Additional Information

Additional information is that the MongoDB database has three collections, one of them is users, second is clubs, third is comments

Once you login/register on the user interface, it brings you to the home page of all the penn clubs. There are two additional buttons for each club. You can choose "more info" button for more information regarding the club. You can choose to post a review of a club
in the "review" button. These reviews will show up in the club info route (comes from clicking "more info" button as well).

On the navigation bar, you can also add a club. Once you add a club, you will be redirected to the home page. The new club should show up there. 

The favorites route ensures that users do not repeat likes by storing liked clubs in a favorite_clubs list. It ensures that the club 
they favorite is not in the favorite clubs list. 

The registration page contains all of the user info that is used to register and what a "user object" should have.

A club record in the database has a name, tags array, and a description.

