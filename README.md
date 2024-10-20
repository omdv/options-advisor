## Summary
Volatility estimator and assignment statistics for SPX. Also Pulumi infrastructure to run [volstats.com](volstats.com).


## How to use
Just go to [volstats.com](volstats.com).

Or you can clone and `flask run`. You will need to comment out the part related to assignment statistics, as it uses my own large processed dataset from CBOE intraday options data.

### Environment variables
| Variable Name     | Description                                      |
|-------------------|--------------------------------------------------|
| `MODE`            | The mode in which the application runs.          |
| `ITM_PICKLE_PATH` | Path to the pickle file for ITM data.            |
| `QUOTES_API_KEY`  | API key for accessing market quotes.             |

### Market API options
| API Name          | Description                                      |
|-------------------|--------------------------------------------------|
| `yahoo`           | Free. Reliability is not great.
| `twelvedata`      | Has free tier but issues with indices since October.
| `fmp`             | My current choice. $20/mo, includes calendar.


## Infra
Setting this up on AWS was a fun weekend project. It runs as lambda container image updating static page on S3, which is then exposed with CloudFront and Route53. It costs less than $2/mo. Domain is another $10/yr.

![AWS](https://raw.githubusercontent.com/omdv/options-advisor/main/aws.svg)

For infra I used Pulumi and generally after this exercise can recommend it as a better alternative to Terraform. Pulumi AI was quite helpful to start and create boilerplate, although it does fail at some niche cases Don't know what LLM they are using, I found that in some cases the vanilla ChatGPT did a better job working with Pulumi documentation.

## References and similar projects:
- [Volatility Trading book](https://www.amazon.com/Volatility-Trading-Website-Euan-Sinclair/dp/1118347137)
- [Volatility Trading repo](https://github.com/jasonstrimpel/volatility-trading)
- [Layman's guide to volatility forecasting](https://saltfinancial.com/static/uploads/2021/05/The%20Laymans%20Guide%20to%20Volatility%20Forecasting.pdf)
