=====
Usage
=====

To use pynations in a project::

	import pynations

	c = pynations.CountryInfo.CountryInfo('us')
	c.states()

OR ::


	from pynations.CountryInfo import CountryInfo
	c = CountryInfo('us')
	c.info()                # Returns all the country information
	c.name()                # Returns country name
	c.states()              # Returns states/provinces in the country
	c.currency()            # Returns currency code and name
	c.languages()           # Returns languages spoken
	c.neighbors()           # Returns neighboring country names
	c.capital()             # Returns the Capital
	c.timezones()           # Returns the list of timezones
	c.population()          # Returns the population
	c.continent()           # Returns the continent

Do note that any valid country name can be used for Instantiation of this class

For getting information on US you could instantiate with ::
    CountryInfo('US'), CountryInfo('usa'), CountryInfo('America'), CountryInfo('amelika'), CountryInfo('feriene steaten') etc.
