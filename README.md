# unicorn-plex-sqlite-streamer
A sidecar container for the Unicorn Transcoder K8s pod to allow for the SQLite DB hosted in ram to be stored in a non-networked PVC

This sidecar is used in the Unicorn Transcoder on K8s Helm chart found [here](https://github.com/Unicorn-K8s/UnicornTrancoder-chart)