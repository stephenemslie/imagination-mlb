# MLB Queueing Service:



## Getting started

In development, the mlb game services can be started with:

    docker-compose up

This runs `django`, `postgres`, `celery` and `redis` in their default configurations as defined by `docker-compose.yml` and `docker-compose.override.yml`.

In production, there are three possible environments that have been considered: `nuc`, `ec2`, and `labs`:

### nuc

This is the on-site server, so named because it ran on an Intel NUC.

```
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.nuc.yml up -d
```

### ec2

This is the off-site read slave of the on-site nuc database which performs writes back to the master on the nuc via a vpn connection. This acts both as a hot backup of the live server, and a means of handling off-site and post-show administration tasks.

```
docker-compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ec2.yml up -d
```

### labs

This is a long-running demo of the mlb game that lives in the imagination lab.

```
docker-compose -f docker-compose.yml -f docker-compose.labs.yml up -d
```

## Users

Three users are created automatically in data migrations: `user`, `mlbtablet`, and `mlbvrgame`. The latter two are required for the tablet and vr game to authenticate with the game server.

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
