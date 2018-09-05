# Lemmiwinks
Lemmiwinks: Web Scrapper

<img src="https://vignette.wikia.nocookie.net/southpark/images/b/b8/Lemmiwinks_%282%29.png/revision/latest?cb=20161218172346" width=110 height=150>


In master branch is currently not working version of Lemmiwings.

The dev branch is used to push broken code, which is under development.

The old-state branch consists of old WPD scrip.

## Docker Configuration
To make Lemmiwings javascript HTTP client work it is necessary to run docker script. The HTTP library supports Selenium standalone scripts.

```bash
$ docker run -d -p 8910:8910 wernight/phantomjs phantomjs --webdriver=8910
# OR
$ docker run -d -p 4444:4444 selenium/standalone-chrome:3.8.1-bohrium
# OR
$ docker run -d -p 4444:4444 selenium/standalone-firefox:3.8.1-bohrium
```
## Links
[selenium](http://selenium-python.readthedocs.io/)

[aiohttp](https://aiohttp.readthedocs.io/en/stable/)

[Dependency Injector](http://python-dependency-injector.ets-labs.org/introduction/di_in_python.html)

[tinycss2](http://tinycss2.readthedocs.io/en/latest/)

[css syntax level 3](https://drafts.csswg.org/css-syntax-3/)

[Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)

[Mozila Archive Format](http://maf.mozdev.org/maff-file-format.html/)

[Jinja](http://jinja.pocoo.org/)

[validators](http://validators.readthedocs.io/en/latest/#)