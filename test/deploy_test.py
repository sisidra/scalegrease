import os
from unittest import TestCase

from mock import patch

from scalegrease.deploy import ArtifactStorage, LocalStorage, MavenStorage
import scalegrease.error


class StorageResolutionTest(TestCase):
    @patch("scalegrease.deploy.os.path.exists", new=lambda (x): x in ["/path/to/local.jar"])
    def test_local_storage_resolve(self):
        storage = ArtifactStorage.resolve("/path/to/local.jar")
        self.assertIsInstance(storage, LocalStorage)

    def test_maven_storage_resolve(self):
        storage = ArtifactStorage.resolve("group:artifact:version")
        self.assertIsInstance(storage, MavenStorage)


class LocalStorageTest(TestCase):
    def test_interface(self):
        storage = LocalStorage("/path/to/local.jar")
        self.assertEqual("/path/to/local.jar", storage.jar_path())

        args = ["--some", "args", "-To=test"]
        self.assertEqual(args, storage.fetch(args))


class MavenStorageTest(TestCase):
    _MVN_CLI_OUTPUT = """
[INFO] Error stacktraces are turned on.
[INFO] Scanning for projects...
[INFO]
[INFO] Using the builder org.apache.maven.lifecycle.internal.builder.singlethreaded.SingleThreadedBuilder with a thread count of 1
[INFO]
[INFO] ------------------------------------------------------------------------
[INFO] Building Maven Stub Project (No POM) 1
[INFO] ------------------------------------------------------------------------
[INFO]
[INFO] --- maven-dependency-plugin:2.8:copy (default-cli) @ standalone-pom ---
[INFO] Configured Artifact: com.spotify:scalegrease:{0}:jar-with-dependencies:jar
[INFO] Copying scalegrease-{1}-jar-with-dependencies.jar to /tmp/path/scalegrease-{2}-jar-with-dependencies.jar
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time: 0.001 s
[INFO] Finished at: 3000-01-01T00:00:00+00:00
[INFO] Final Memory: XM/YM
[INFO] ------------------------------------------------------------------------
    """

    def test_not_fetched(self):
        storage = MavenStorage("group:artifact:version")
        self.assertRaises(scalegrease.error.Error, storage.jar_path)

    def test_parse_args(self):
        storage = MavenStorage("group:artifact")
        rest = ["--some", "args", "-To=test"]

        offline, actual = storage._parse_args(rest)
        self.assertEqual(rest, actual)
        self.assertFalse(offline)

        args2 = ["--mvn-offline", "--some", "args", "-To=test"]
        offline, actual = storage._parse_args(args2)
        self.assertEqual(rest, actual)
        self.assertTrue(offline)

        args3 = ["-o", "--some", "args", "-To=test"]
        offline, actual = storage._parse_args(args3)
        self.assertEqual(rest, actual)
        self.assertTrue(offline)

    @patch("scalegrease.deploy.tempfile.mkdtemp", new=lambda (prefix): os.path.join("/tmp/path"))
    @patch("scalegrease.deploy.shutil.rmtree", new=lambda(path): None)
    @patch("scalegrease.deploy.os.environ", new={"HOME": "/home/scalegrease"})
    @patch("scalegrease.deploy.system.check_output",
           new=lambda(args): MavenStorageTest._MVN_CLI_OUTPUT.format(
               "LATEST", "0.0.1-SNAPSHOT", "0.0.1-30000101T0000"))
    def test_fetch_parsing(self):
        storage = MavenStorage("com.spotify:scalegrease")
        storage.fetch([])
        self.assertEqual("/home/scalegrease/.m2/repository/com/spotify/scalegrease/0.0.1-SNAPSHOT/scalegrease-0.0.1-30000101T0000-jar-with-dependencies.jar", storage.jar_path())
        self.assertEqual("com.spotify:scalegrease:LATEST:jar:jar-with-dependencies", storage.spec())
