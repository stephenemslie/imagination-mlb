# MLB Queueing Service:



## Getting started

    docker-compose build
    docker-compose up django


### Running in production:

    docker-compose build
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d django


## Game states

### New

Every game starts in this state

### Queued

`POST /games/<id>/queue/`

The above endpoint puts a game into the `queued` state. Games in the `new` state can be queued, and games in the `recalled` state can be re-queued.

### Recalled

`POST /games/<id>/recall/`

This puts the game into a `recalled` state, and triggers an sms to be sent to the user attached to the game. Users can only be recalled if they were `queued` first.

### Confirmed

`POST /games/<id>/confirm/`

A post to this method indicates that a user is ready to play the game, either because they have been recalled, or because they have just arrived and the queue is empty. You can confirm a user that is either `new` or `recalled`.

### Playing

`POST /games/<id>/play/`

When a user has been confirmed, they are ready to play the game, which is started by a request this endpoint. The game is now in a `playing` state.

### Completed

`POST /games/<id>/complete/`

Once the game has been played and the scores are ready, the game is completed. This is indicated by sending a `POST` request to the above endpoing with the following data `score`, `distance`, `homeruns` in the request body.
