# Lemmiwinks
Lemmiwinks: Web Crawler

In master branch is currently not working version of Lemmiwings. 

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
