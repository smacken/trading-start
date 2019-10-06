# Trading Start - Trading system data importer

Trading data within your broker doesn't give you enough information to run a trading system.
This imports your trading data from your broker into your trading system so that you can then
more accurately analyse your trading portfolio.

[![Codecov Coverage](https://img.shields.io/codecov/c/github/smacken/trading-start/&lt;master>.svg?style=flat-square)](https://codecov.io/gh/smaken/trading-start/)

## Getting Started

Clone or download the trading-start importer.

Configure where your trading platform is to import your data

```
config.json
```

Download & Run to import trading data from your broker.

```bash
node index.js --file --holdings --transactions --account
```

In order to pull data directly from the broker, omit the --file flag
You will be asked for credentials in order to retrieve trading data.
```bash
node index.js --holdings
```
### Prerequisites

Node.js/npm
* [NodeJs](https://nodejs.org/en/download/)

### Installing

Download/clone trading-start. Add to path.

```
git clone https://github.com/smacken/trading-start.git
```

Configure the location/destination of your trading system to import data to

```
config.json > 'sourcePath', 'destinationPath'
```
From Commsec data will usually come to /Downloads as Holdings(*).csv, Transactions(*).csv, or CSVData.csv

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

## Deployment

Add additional notes about how to deploy this on a live system

## Built With

* [Commsec](https://github.com/Malvineous/commsecjs) - Commsec API

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Authors

* **Scott Mackenzie** - *Initial work* - [PurpleBooth](https://github.com/smacken)

See also the list of [contributors](https://github.com/trading-start/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* mmmm
