// This file contains build specifications for Spotify internal CI/CD pipeline.  It can be safely
// ignored.

@Grab(group = 'com.spotify', module = 'pipeline-conventions', version = '0.0.6', changing = true)

import com.spotify.pipeline.*

def VERSION = '0.1'
def EPOCH = '0'

use(Pipeline, dist.Deb) {
    pipeline {
        stage('Squeeze build') {
            pipelineVersion("${EPOCH}:${VERSION}")
            buildPackage(distro: 'unstable', release: 'squeeze')
        }
        stage('Squeeze upload') {
            uploadPackage(distro: 'unstable', release: 'squeeze')
            uploadPackage(distro: 'stable', release: 'squeeze')
        }
        stage('Trusty build') {
            buildPackage(distro: 'unstable', release: 'trusty')
        }
        stage('Trusty upload') {
            uploadPackage(distro: 'unstable', release: 'trusty')
            uploadPackage(distro: 'stable', release: 'trusty')
        }
    }
}
