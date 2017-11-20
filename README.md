# serverless-umbrella-reminder-sms

This is an [AWS Lambda](https://aws.amazon.com/lambda/) function, [Powered by Dark Sky](https://darksky.net/poweredby/), that checks the forecast at a predetermined time each day, and sends you an SMS [Amazon Simple Notification Service](https://aws.amazon.com/sns/) if heavy rain is in the forecast.

You need to request your own [Dark Sky API](https://darksky.net/dev) key for this app to work. Dark Sky permits a generous 1000 free calls per day, which is more than enough for the one check required by this app. AWS SNS includes up to 100 free SMS notifications per month (at least in the United States; support for other countries may vary), and offers a substantial free tier for AWS Lambda, so this may be completely cost-free if you're just getting started with these tools, and should be fairly inexpensive even if you are already a heavy user of AWS and Dark Sky.

Please note that [SNS only supports SMS messaging in a subset of regions](http://docs.aws.amazon.com/sns/latest/dg/sms_supported-countries.html). Please see the linked support document to ensure you deploy this application in a supported region.

## Deployment

Deploying this serverless app to your AWS account is quick and easy using [AWS CloudFormation](https://aws.amazon.com/cloudformation/).

### Packaging

First, let's download the required dependencies. We need to package the [pytz](http://pytz.sourceforge.net) library into our Lambda deployment package to get accurate local time.

```sh
pip3 install -r requirements.txt -t app
```

With the [AWS CLI](https://aws.amazon.com/cli/) installed, run the following command to upload the code to S3. You need to re-run this if you change the code in `archiver.py`. Be sure to set `DEPLOYMENT_S3_BUCKET` to a **bucket you own**; CloudFormation will copy the code function into a ZIP file in this S3 bucket, which can be deployed to AWS Lambda in the following steps.

```sh
DEPLOYMENT_S3_BUCKET="YOUR_S3_BUCKET"
aws cloudformation package --template-file cloudformation.yaml --s3-bucket $DEPLOYMENT_S3_BUCKET \
  --output-template-file cloudformation-packaged.yaml
```

Now you will have `cloudformation-packaged.yaml`, which contains the full path to the ZIP file created by the previous step.

### Configuring

Next, let's set the required configuration. You can set the following parameters:

 * `PHONE_NUMBER` is the recipient of the weather alert. Use [E.164](https://en.wikipedia.org/wiki/E.164) (e.g. +15555550100) format.
 * `WEATHER_LOCATION` is a latitude, longitude pair of where you live/work. One way to find this is to look up your city on Wikipedia, click the coordinates in the top right of the page, and then copy the "Decimal" coordinates from the top of the linked page.
 * `TIME_ZONE` is your [local time zone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
 * `DARK_SKY_KEY` is a [Dark Sky API](https://darksky.net/dev) key. They have a generous free tier, so sign up and **enter your own key** here.
 * `MESSAGE_LOCAL_TIME` is the local time to check the weather. This must be at a fifteen-minute mark with a zero padded hour, e.g. 08:15.

```sh
STACK_NAME="serverless-umbrella-reminder-sms"
PHONE_NUMBER="+15555555555"
WEATHER_LOCATION="47.62,-122.34"
TIME_ZONE="America/Los_Angeles"
DARK_SKY_KEY="00000000000000000000000000000000"
MESSAGE_LOCAL_TIME="08:00"
```

With these configuration parameters defined, we can call `cloudformation deploy` to create the necessary resources in your AWS account:

```sh
aws cloudformation deploy --template-file cloudformation-packaged.yaml --capabilities CAPABILITY_IAM \
  --parameter-overrides \
  "PhoneNumber=$PHONE_NUMBER" \
  "WeatherLocation=$WEATHER_LOCATION" \
  "TimeZone=$TIME_ZONE" \
  "DarkSkyKey=$DARK_SKY_KEY" \
  "MessageLocalTime=$MESSAGE_LOCAL_TIME" \
  --stack-name $STACK_NAME
````

If all went well, your stack has now been created. Next time the clock strikes `$MESSAGE_LOCAL_TIME`, if rain is in the forecast, you should look forward to a notification on your phone!
