# RSM

RSM (pronoucned "rizz 'em") (Really Simple Mirror) is the bulletproof mirror you've been looking for.

Throw all the packages you want to play with in `wishlist.txt`, tweak the Python versions and desired platforms in `rsm.py`.

Then run:

```sh
uv run python rsm.py
```

to generate the requirements, and then:

```sh
uv run bandersnatch -c bd.conf mirror
```

to download. Lastly, to serve:

```sh
uv run python -m http.server 8080 --directory ./simple/web/
```

There is a `systemd` service ready in `private_mirror.service` to be registered at your leisure. Save to `/etc/systemd/system/private-mirror.service` and then:

```sh
sudo systemctl daemon-reload
sudo systemctl enable private-mirror
sudo systemctl start private-mirror
sudo systemctl status private-mirror
```

To set up uv, add the following to the user wide `uv.toml`:

```toml
[[index]]
url = "http://<IPADDR>:8080/simple/"
default = true
```

RSM also downloads Python versions, but this is WIP. 