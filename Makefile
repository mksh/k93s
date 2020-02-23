.PHONY: qa

K_93_CONFIG=.k93s.working.config

qa:
	make test
	make flake

config:
	python3 -m k93s --config-file="$(K_93_CONFIG)" config

ensureconfig:
	test ! -f "$(K_93_CONFIG)" && make config K_93_CONFIG="$(K_93_CONFIG)"

up:
	-make ensureconfig
	python3 -m k93s --config-file="$(K_93_CONFIG)" kubernetes

down:
	python3 -m k93s --config-file="$(K_93_CONFIG)" teardown

test:
	python3 -m nose -sv --nologcapture k93s.test --with-cov --cov=k93s --cov-report=term-missing

flake:
	flake8 k93s
