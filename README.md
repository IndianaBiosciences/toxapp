# IBRI's Toxicogenomic Platform

This platform provides tools and workflows for early risk assessment using toxicogenomics based on publically available data sources or other data sets that have been released in support of this platform. It is expected that this platform will accelerate the development of the supporting science and increase adoption of new risks assessment tools by the broader research community.

Currently this platform is in the early prototype phase to establish secure collaboration tools for participating organizations and to define the conceptual architecture and framework that leverages and/or integrates with other efforts in toxicogenomics. The first working implementation of this platform delivers a full end-to-end workflow from data to visualizations with to-be-defined research methods based on the best practices of the Sponsor(s).

## Key References
* J J Sutherland, Y W Webster, J A Willy, G H Searfoss, K M Goldstein, A R Irizarry, D G Hall, and J L Stevens, 'Toxicogenomic module associations with pathogenesis (TXG-MAP): A network based approach to understanding drug toxicity', The Pharmacogenomics Journal, [Advance Online Publication](https://www.nature.com/tpj/journal/vaop/ncurrent/full/tpj201717a.html)

* Jeffrey J Sutherland  James L Stevens  Kamin Johnson  Navin Elango  Yue W Webster Bradley J Mills  Daniel H Robertson, 'A novel open access web portal for integrating mechanistic and toxicogenomic study results', Toxicological Sciences, [Advance Online Publication](https://academic.oup.com/toxsci/advance-article/doi/10.1093/toxsci/kfz101/5478579)

## Getting Started
Visit our current deployment here: [link](http://ctox.indianabiosciences.org)

If you signup you will recieve an email notifying you of granted access.



### Documentation

[Link to deployment documentation](../master/documentation/Requirements_and_Installation.docx)

### Running the tests

The tests run from runner.py and will go through in testing each pipeline including email, rabbitmq, celery, our data processes, and your R installation

## Built With

* [Django](https://www.djangoproject.com/) - The web framework used
* [PSQL](https://www.postgresql.org/) - Database Backend

## Contributing

TODO

## Versioning

TODO

## Authors

* **Daniel H Robertson ** - [dhrobertson](https://github.com/dhrobertson)
* **Jeff Sutherland ** - [sutherlandjeff](https://github.com/sutherlandjeff)
* **Brad Mills ** - [bradjmills](https://github.com/bradjmills)


See also the list of [contributors](https://github.com/IndianaBiosciences/toxapp/contributors) who participated in this project.

## License
[Apache-2.0](https://github.com/IndianaBiosciences/toxapp/blob/master/LICENSE)

## Inquiries
Contact Brad Mills at bmills(at)indianabiosciences(dot)org
