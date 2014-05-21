import json
import logging
import urllib
import urllib2


def download(artifact, tmp_dir, version):
    # TODO: Don't use artifactory REST, use maven instead.
    repo_url = "https://artifactory.spotify.net/artifactory/api/storage/libs-release-local"
    artifact_url = "%s/%s" % (repo_url, artifact.path())
    repo_info = fetch_repo_info(artifact_url)
    versions = [ch["uri"][1:] for ch in repo_info["children"]]
    latest_version = sorted(versions, key=lambda v: map(int, v.split('.')))[-1]

    jar_base = ("%s-%s-jar-with-dependencies.jar" % (artifact.artifact_id(), latest_version))
    jar_info_url = ("%s/%s/%s" % (artifact_url, latest_version, jar_base))
    jar_info = fetch_repo_info(jar_info_url)
    jar_url = jar_info["downloadUri"]
    jar_local = "%s/%s" % (tmp_dir, jar_base)
    urllib.urlretrieve(jar_url, filename=jar_local)
    return jar_local


def fetch_repo_info(url):
    logging.debug("Retrieving %s", url)
    rsp = urllib2.urlopen(url)
    contents = rsp.read()
    repo_info = json.loads(contents)
    return repo_info
