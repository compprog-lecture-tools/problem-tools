#!/usr/bin/env bash
docker-compose exec judge-web /opt/domjudge/domserver/webapp/bin/console doctrine:fixture:load --append --group=HpiSettingsFixture
docker-compose exec judge-web /opt/domjudge/domserver/webapp/bin/console doctrine:fixture:load --append --group=HpiProblemDevSetupFixture
