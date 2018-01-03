import datetime
import json

import scrapy

from stackoverflow.items import JobItem


class JobSpider(scrapy.Spider):
    name = "jobs"
    allowed_domains = ["stackoverflow.com"]
    base_url = "https://stackoverflow.com"
    job_base_url = "https://stackoverflow.com/jobs/"
    start_time = datetime.datetime.now()

    def start_requests(self):
        # Through the browser says that there are 1545 jobs 
        # ( 1500 / 25 jobs per page = 60 pages)
        # but when using wget or scrapy page 100 contain josb
        # and html says that there are 3560 jobs
        for i in xrange(1, 100):
            yield self.make_requests_from_url(
                "https://stackoverflow.com/jobs?pg=%d" % i)

    def parse(self, response):
        """
        Get job id
        Returns request object for job url
        """
        # looks for <a> elements with a data-jobid attribute
        # <a class="fav-toggle" data-jobid="81955"
        # href="/jobs/togglefavorite/81955?returnUrl=%2fjobs"></a>
        jobs_id = response.css('div').xpath('@data-jobid').extract()

        # Yield a request object to the job detail page
        for job_id in jobs_id:
            job = JobItem()
            job['id'] = job_id
            job_url = self.job_base_url + job_id
            request = scrapy.Request(job_url,
                                     callback=self.parse_job_detail_page)
            request.meta['job'] = job
            yield request

    def parse_job_detail_page(self, response):
        """
        Get job url, date, title, employer, tags, location and description
        Returns job item to pipeline
        """
        x = response.xpath("//script[@type='application/ld+json']")
        y = x[0].root.text
        z = json.loads(y)
        job = response.meta['job']
        job['url'] = response.url
        job['inAWS'] = False
        job['date'] = datetime.datetime.strptime(z['datePosted'],'%Y-%m-%d').isoformat()
        job['title'] = z['title'].replace('/','-')
        job['employer'] = z['hiringOrganization']['name']
        job['tags'] = response.css('.-technologies .-tags a::text').extract()
        location = response.css('.-location::text')[0].extract().strip().replace('- \n', '')
        if location == 'No office location':
            job['location'] = 'Remote'
        else:
            job['location'] = location
            # Use xpath selectors and //text() for getting all the text in different levels
        job['description'] = response.xpath('//div[@class="description"]').extract_first()

        return job
