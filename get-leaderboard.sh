URL=https://release.imagination.net/mlb-app-event-queue-leaderboard
mkdir -p game/static/leaderboard
cd game/static/leaderboard
export LB_VERSION=`curl --digest -u $RELEASE_AUTH $URL/package.json | jp -u version`
curl --digest -u $RELEASE_AUTH $URL/mlb-app-event-queue-leaderboard-${LB_VERSION}.tar.gz | tar xzvf -
