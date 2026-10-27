"""Real countries and cities that host the fictional golf world.

Every course and event is fictional, but each one is placed in a real city where that style of golf
makes sense. Climate decides which weeks of the year a city can host competitive golf:

    temperate / oceanic / continental  northern summer season (southern summer below the equator)
    mediterranean / subtropical        year-round
    tropical                           year-round
    desert                             cool-season only (the summer is too hot)
    alpine                             short high-summer season
"""
from __future__ import annotations

from dataclasses import dataclass

REGIONS = ('North America', 'Latin America', 'Europe', 'Middle East', 'Africa', 'Asia', 'Oceania')


@dataclass(frozen=True)
class Country:
    name: str
    region: str
    south: bool          # southern hemisphere (seasons reversed)
    golf: float          # relative size of the country's golf scene (USA = 10)


@dataclass(frozen=True)
class City:
    name: str
    country: str
    climate: str
    coastal: bool = False


COUNTRIES = {c.name: c for c in (
    Country('USA', 'North America', False, 10.0), Country('Canada', 'North America', False, 3.0),
    Country('Mexico', 'Latin America', False, 1.2), Country('Brazil', 'Latin America', True, 0.6),
    Country('Argentina', 'Latin America', True, 1.0), Country('Chile', 'Latin America', True, 0.5),
    Country('Colombia', 'Latin America', False, 0.6), Country('Peru', 'Latin America', True, 0.3),
    Country('England', 'Europe', False, 5.0), Country('Scotland', 'Europe', False, 3.0),
    Country('Ireland', 'Europe', False, 2.0), Country('Northern Ireland', 'Europe', False, 1.0),
    Country('Wales', 'Europe', False, 0.8), Country('Spain', 'Europe', False, 2.0),
    Country('Portugal', 'Europe', False, 1.0), Country('France', 'Europe', False, 1.5),
    Country('Germany', 'Europe', False, 1.8), Country('Netherlands', 'Europe', False, 1.0),
    Country('Belgium', 'Europe', False, 0.6), Country('Denmark', 'Europe', False, 0.9),
    Country('Sweden', 'Europe', False, 1.6), Country('Norway', 'Europe', False, 0.6),
    Country('Finland', 'Europe', False, 0.5), Country('Italy', 'Europe', False, 0.8),
    Country('Austria', 'Europe', False, 0.6), Country('Switzerland', 'Europe', False, 0.6),
    Country('Czechia', 'Europe', False, 0.4), Country('Poland', 'Europe', False, 0.3),
    Country('Turkey', 'Europe', False, 0.3),
    Country('United Arab Emirates', 'Middle East', False, 0.8), Country('Qatar', 'Middle East', False, 0.3),
    Country('Saudi Arabia', 'Middle East', False, 0.4), Country('Bahrain', 'Middle East', False, 0.2),
    Country('Oman', 'Middle East', False, 0.2),
    Country('South Africa', 'Africa', True, 2.5), Country('Kenya', 'Africa', True, 0.5),
    Country('Morocco', 'Africa', False, 0.5), Country('Nigeria', 'Africa', False, 0.3),
    Country('Egypt', 'Africa', False, 0.3), Country('Zimbabwe', 'Africa', True, 0.4),
    Country('Namibia', 'Africa', True, 0.2), Country('Zambia', 'Africa', True, 0.2),
    Country('Mauritius', 'Africa', True, 0.2),
    Country('Japan', 'Asia', False, 5.0), Country('South Korea', 'Asia', False, 3.0),
    Country('China', 'Asia', False, 2.0), Country('Taiwan', 'Asia', False, 0.8),
    Country('India', 'Asia', False, 1.2), Country('Thailand', 'Asia', False, 1.2),
    Country('Malaysia', 'Asia', False, 0.7), Country('Singapore', 'Asia', False, 0.4),
    Country('Philippines', 'Asia', False, 0.6), Country('Indonesia', 'Asia', True, 0.5),
    Country('Vietnam', 'Asia', False, 0.4),
    Country('Australia', 'Oceania', True, 4.0), Country('New Zealand', 'Oceania', True, 1.2),
    Country('Fiji', 'Oceania', True, 0.2),
)}

_C = City
CITIES = (
    # USA
    _C('Athens, Georgia', 'USA', 'subtropical'), _C('Atlanta, Georgia', 'USA', 'subtropical'),
    _C('Augusta, Georgia', 'USA', 'subtropical'), _C('Savannah, Georgia', 'USA', 'subtropical', True),
    _C('Orlando, Florida', 'USA', 'subtropical'), _C('Jacksonville, Florida', 'USA', 'subtropical', True),
    _C('Palm Beach Gardens, Florida', 'USA', 'subtropical', True), _C('Miami, Florida', 'USA', 'tropical', True),
    _C('Tampa, Florida', 'USA', 'subtropical', True), _C('Naples, Florida', 'USA', 'subtropical', True),
    _C('Pinehurst, North Carolina', 'USA', 'subtropical'), _C('Charlotte, North Carolina', 'USA', 'subtropical'),
    _C('Greensboro, North Carolina', 'USA', 'subtropical'), _C('Myrtle Beach, South Carolina', 'USA', 'subtropical', True),
    _C('Hilton Head Island, South Carolina', 'USA', 'subtropical', True), _C('Kiawah Island, South Carolina', 'USA', 'subtropical', True),
    _C('Nashville, Tennessee', 'USA', 'temperate'), _C('Memphis, Tennessee', 'USA', 'temperate'),
    _C('Birmingham, Alabama', 'USA', 'subtropical'), _C('New Orleans, Louisiana', 'USA', 'subtropical'),
    _C('Dallas, Texas', 'USA', 'subtropical'), _C('Fort Worth, Texas', 'USA', 'subtropical'),
    _C('Houston, Texas', 'USA', 'subtropical'), _C('San Antonio, Texas', 'USA', 'subtropical'),
    _C('Austin, Texas', 'USA', 'subtropical'), _C('Oklahoma City, Oklahoma', 'USA', 'temperate'),
    _C('Tulsa, Oklahoma', 'USA', 'temperate'), _C('Scottsdale, Arizona', 'USA', 'desert'),
    _C('Phoenix, Arizona', 'USA', 'desert'), _C('Tucson, Arizona', 'USA', 'desert'),
    _C('Las Vegas, Nevada', 'USA', 'desert'), _C('Palm Springs, California', 'USA', 'desert'),
    _C('San Diego, California', 'USA', 'mediterranean', True), _C('Los Angeles, California', 'USA', 'mediterranean', True),
    _C('Monterey, California', 'USA', 'mediterranean', True), _C('San Francisco, California', 'USA', 'mediterranean', True),
    _C('Sacramento, California', 'USA', 'mediterranean'), _C('Portland, Oregon', 'USA', 'oceanic'),
    _C('Bandon, Oregon', 'USA', 'oceanic', True), _C('Seattle, Washington', 'USA', 'oceanic', True),
    _C('Denver, Colorado', 'USA', 'continental'), _C('Vail, Colorado', 'USA', 'alpine'),
    _C('Salt Lake City, Utah', 'USA', 'continental'), _C('Boise, Idaho', 'USA', 'continental'),
    _C('Chicago, Illinois', 'USA', 'continental'), _C('Detroit, Michigan', 'USA', 'continental'),
    _C('Grand Rapids, Michigan', 'USA', 'continental'), _C('Columbus, Ohio', 'USA', 'continental'),
    _C('Cincinnati, Ohio', 'USA', 'continental'), _C('Cleveland, Ohio', 'USA', 'continental'),
    _C('Indianapolis, Indiana', 'USA', 'continental'), _C('Muncie, Indiana', 'USA', 'continental'),
    _C('Milwaukee, Wisconsin', 'USA', 'continental'), _C('Kohler, Wisconsin', 'USA', 'continental'),
    _C('Minneapolis, Minnesota', 'USA', 'continental'), _C('St. Louis, Missouri', 'USA', 'continental'),
    _C('Kansas City, Missouri', 'USA', 'continental'), _C('Omaha, Nebraska', 'USA', 'continental'),
    _C('Louisville, Kentucky', 'USA', 'temperate'), _C('Pittsburgh, Pennsylvania', 'USA', 'continental'),
    _C('Philadelphia, Pennsylvania', 'USA', 'temperate'), _C('Southampton, New York', 'USA', 'temperate', True),
    _C('Rochester, New York', 'USA', 'continental'), _C('Boston, Massachusetts', 'USA', 'continental', True),
    _C('Hartford, Connecticut', 'USA', 'continental'), _C('Bethesda, Maryland', 'USA', 'temperate'),
    _C('Richmond, Virginia', 'USA', 'temperate'), _C('Honolulu, Hawaii', 'USA', 'tropical', True),
    _C('Lahaina, Hawaii', 'USA', 'tropical', True),
    # Canada
    _C('Toronto, Ontario', 'Canada', 'continental'), _C('Ottawa, Ontario', 'Canada', 'continental'),
    _C('Montreal, Quebec', 'Canada', 'continental'), _C('Vancouver, British Columbia', 'Canada', 'oceanic', True),
    _C('Calgary, Alberta', 'Canada', 'continental'), _C('Halifax, Nova Scotia', 'Canada', 'continental', True),
    # Latin America
    _C('Mexico City', 'Mexico', 'subtropical'), _C('Cancún', 'Mexico', 'tropical', True),
    _C('San José del Cabo', 'Mexico', 'desert', True), _C('Guadalajara', 'Mexico', 'subtropical'),
    _C('Monterrey', 'Mexico', 'subtropical'), _C('São Paulo', 'Brazil', 'subtropical'),
    _C('Rio de Janeiro', 'Brazil', 'tropical', True), _C('Florianópolis', 'Brazil', 'subtropical', True),
    _C('Buenos Aires', 'Argentina', 'temperate', True), _C('Córdoba', 'Argentina', 'temperate'),
    _C('Mar del Plata', 'Argentina', 'oceanic', True), _C('Santiago', 'Chile', 'mediterranean'),
    _C('Viña del Mar', 'Chile', 'mediterranean', True), _C('Bogotá', 'Colombia', 'tropical'),
    _C('Medellín', 'Colombia', 'tropical'), _C('Cartagena', 'Colombia', 'tropical', True),
    _C('Lima', 'Peru', 'desert', True),
    # Europe
    _C('London', 'England', 'oceanic'), _C('Virginia Water', 'England', 'oceanic'),
    _C('Sunningdale', 'England', 'oceanic'), _C('Southport', 'England', 'oceanic', True),
    _C('Hoylake', 'England', 'oceanic', True), _C('Sandwich', 'England', 'oceanic', True),
    _C('Birmingham', 'England', 'oceanic'), _C('Manchester', 'England', 'oceanic'),
    _C('Newcastle upon Tyne', 'England', 'oceanic', True), _C('Bristol', 'England', 'oceanic'),
    _C('Woodhall Spa', 'England', 'oceanic'), _C('St Andrews', 'Scotland', 'oceanic', True),
    _C('Edinburgh', 'Scotland', 'oceanic', True), _C('Glasgow', 'Scotland', 'oceanic'),
    _C('Carnoustie', 'Scotland', 'oceanic', True), _C('Troon', 'Scotland', 'oceanic', True),
    _C('North Berwick', 'Scotland', 'oceanic', True), _C('Gleneagles', 'Scotland', 'oceanic'),
    _C('Aberdeen', 'Scotland', 'oceanic', True), _C('Inverness', 'Scotland', 'oceanic', True),
    _C('Dublin', 'Ireland', 'oceanic', True), _C('Cork', 'Ireland', 'oceanic', True),
    _C('Killarney', 'Ireland', 'oceanic'), _C('Galway', 'Ireland', 'oceanic', True),
    _C('Ballybunion', 'Ireland', 'oceanic', True), _C('Belfast', 'Northern Ireland', 'oceanic', True),
    _C('Portrush', 'Northern Ireland', 'oceanic', True), _C('Newcastle, County Down', 'Northern Ireland', 'oceanic', True),
    _C('Cardiff', 'Wales', 'oceanic', True), _C('Newport', 'Wales', 'oceanic'), _C('Tenby', 'Wales', 'oceanic', True),
    _C('Madrid', 'Spain', 'mediterranean'), _C('Barcelona', 'Spain', 'mediterranean', True),
    _C('Marbella', 'Spain', 'mediterranean', True), _C('Málaga', 'Spain', 'mediterranean', True),
    _C('Valencia', 'Spain', 'mediterranean', True), _C('Seville', 'Spain', 'mediterranean'),
    _C('Palma de Mallorca', 'Spain', 'mediterranean', True), _C('Santa Cruz de Tenerife', 'Spain', 'subtropical', True),
    _C('Lisbon', 'Portugal', 'mediterranean', True), _C('Faro', 'Portugal', 'mediterranean', True),
    _C('Porto', 'Portugal', 'oceanic', True), _C('Paris', 'France', 'oceanic'),
    _C('Bordeaux', 'France', 'oceanic'), _C('Lyon', 'France', 'continental'),
    _C('Nice', 'France', 'mediterranean', True), _C('Biarritz', 'France', 'oceanic', True),
    _C('Munich', 'Germany', 'continental'), _C('Hamburg', 'Germany', 'oceanic'),
    _C('Berlin', 'Germany', 'continental'), _C('Düsseldorf', 'Germany', 'oceanic'),
    _C('Frankfurt', 'Germany', 'continental'), _C('Amsterdam', 'Netherlands', 'oceanic'),
    _C('The Hague', 'Netherlands', 'oceanic', True), _C('Antwerp', 'Belgium', 'oceanic'),
    _C('Brussels', 'Belgium', 'oceanic'), _C('Copenhagen', 'Denmark', 'oceanic', True),
    _C('Aarhus', 'Denmark', 'oceanic', True), _C('Stockholm', 'Sweden', 'continental', True),
    _C('Gothenburg', 'Sweden', 'oceanic', True), _C('Malmö', 'Sweden', 'oceanic', True),
    _C('Oslo', 'Norway', 'continental'), _C('Bergen', 'Norway', 'oceanic', True),
    _C('Helsinki', 'Finland', 'continental', True), _C('Rome', 'Italy', 'mediterranean'),
    _C('Milan', 'Italy', 'continental'), _C('Turin', 'Italy', 'continental'),
    _C('Vienna', 'Austria', 'continental'), _C('Salzburg', 'Austria', 'continental'),
    _C('Innsbruck', 'Austria', 'alpine'), _C('Geneva', 'Switzerland', 'continental'),
    _C('Zürich', 'Switzerland', 'continental'), _C('Crans-Montana', 'Switzerland', 'alpine'),
    _C('Prague', 'Czechia', 'continental'), _C('Warsaw', 'Poland', 'continental'),
    _C('Gdańsk', 'Poland', 'continental', True), _C('Antalya', 'Turkey', 'mediterranean', True),
    _C('Istanbul', 'Turkey', 'mediterranean', True),
    # Middle East
    _C('Dubai', 'United Arab Emirates', 'desert', True), _C('Abu Dhabi', 'United Arab Emirates', 'desert', True),
    _C('Ras Al Khaimah', 'United Arab Emirates', 'desert', True), _C('Doha', 'Qatar', 'desert', True),
    _C('Riyadh', 'Saudi Arabia', 'desert'), _C('Jeddah', 'Saudi Arabia', 'desert', True),
    _C('Manama', 'Bahrain', 'desert', True), _C('Muscat', 'Oman', 'desert', True),
    # Africa
    _C('Johannesburg', 'South Africa', 'subtropical'), _C('Pretoria', 'South Africa', 'subtropical'),
    _C('Cape Town', 'South Africa', 'mediterranean', True), _C('Durban', 'South Africa', 'subtropical', True),
    _C('George', 'South Africa', 'oceanic', True), _C('Sun City', 'South Africa', 'subtropical'),
    _C('Gqeberha', 'South Africa', 'subtropical', True), _C('East London', 'South Africa', 'subtropical', True),
    _C('Nairobi', 'Kenya', 'subtropical'), _C('Mombasa', 'Kenya', 'tropical', True),
    _C('Nakuru', 'Kenya', 'subtropical'), _C('Rabat', 'Morocco', 'mediterranean', True),
    _C('Marrakesh', 'Morocco', 'desert'), _C('Agadir', 'Morocco', 'desert', True),
    _C('Lagos', 'Nigeria', 'tropical', True), _C('Abuja', 'Nigeria', 'tropical'),
    _C('Cairo', 'Egypt', 'desert'), _C('Sharm El Sheikh', 'Egypt', 'desert', True),
    _C('Harare', 'Zimbabwe', 'subtropical'), _C('Windhoek', 'Namibia', 'desert'),
    _C('Lusaka', 'Zambia', 'subtropical'), _C('Port Louis', 'Mauritius', 'tropical', True),
    # Asia
    _C('Tokyo', 'Japan', 'temperate'), _C('Chiba', 'Japan', 'temperate', True),
    _C('Yokohama', 'Japan', 'temperate', True), _C('Osaka', 'Japan', 'temperate'),
    _C('Kobe', 'Japan', 'temperate', True), _C('Nagoya', 'Japan', 'temperate'),
    _C('Sapporo', 'Japan', 'continental'), _C('Fukuoka', 'Japan', 'temperate', True),
    _C('Hiroshima', 'Japan', 'temperate', True), _C('Sendai', 'Japan', 'temperate', True),
    _C('Karuizawa', 'Japan', 'alpine'), _C('Miyazaki', 'Japan', 'subtropical', True),
    _C('Seoul', 'South Korea', 'continental'), _C('Incheon', 'South Korea', 'continental', True),
    _C('Busan', 'South Korea', 'temperate', True), _C('Jeju City', 'South Korea', 'temperate', True),
    _C('Daegu', 'South Korea', 'continental'), _C('Shanghai', 'China', 'subtropical', True),
    _C('Shenzhen', 'China', 'subtropical', True), _C('Beijing', 'China', 'continental'),
    _C('Haikou', 'China', 'tropical', True), _C('Xiamen', 'China', 'subtropical', True),
    _C('Kunming', 'China', 'temperate'), _C('Taipei', 'Taiwan', 'subtropical'),
    _C('Taichung', 'Taiwan', 'subtropical'), _C('Kaohsiung', 'Taiwan', 'tropical', True),
    _C('New Delhi', 'India', 'subtropical'), _C('Gurugram', 'India', 'subtropical'),
    _C('Mumbai', 'India', 'tropical', True), _C('Bengaluru', 'India', 'tropical'),
    _C('Kolkata', 'India', 'tropical'), _C('Chandigarh', 'India', 'subtropical'),
    _C('Bangkok', 'Thailand', 'tropical'), _C('Pattaya', 'Thailand', 'tropical', True),
    _C('Hua Hin', 'Thailand', 'tropical', True), _C('Phuket', 'Thailand', 'tropical', True),
    _C('Chiang Mai', 'Thailand', 'tropical'), _C('Kuala Lumpur', 'Malaysia', 'tropical'),
    _C('George Town, Penang', 'Malaysia', 'tropical', True), _C('Johor Bahru', 'Malaysia', 'tropical', True),
    _C('Singapore', 'Singapore', 'tropical', True), _C('Manila', 'Philippines', 'tropical', True),
    _C('Cebu City', 'Philippines', 'tropical', True), _C('Jakarta', 'Indonesia', 'tropical', True),
    _C('Denpasar, Bali', 'Indonesia', 'tropical', True), _C('Ho Chi Minh City', 'Vietnam', 'tropical'),
    _C('Da Nang', 'Vietnam', 'tropical', True), _C('Hanoi', 'Vietnam', 'subtropical'),
    # Oceania
    _C('Melbourne', 'Australia', 'oceanic', True), _C('Sydney', 'Australia', 'subtropical', True),
    _C('Brisbane', 'Australia', 'subtropical', True), _C('Gold Coast', 'Australia', 'subtropical', True),
    _C('Perth', 'Australia', 'mediterranean', True), _C('Adelaide', 'Australia', 'mediterranean', True),
    _C('Hobart', 'Australia', 'oceanic', True), _C('Cairns', 'Australia', 'tropical', True),
    _C('Canberra', 'Australia', 'oceanic'), _C('Auckland', 'New Zealand', 'oceanic', True),
    _C('Christchurch', 'New Zealand', 'oceanic', True), _C('Queenstown', 'New Zealand', 'alpine'),
    _C('Wellington', 'New Zealand', 'oceanic', True), _C('Nadi', 'Fiji', 'tropical', True),
    _C('Suva', 'Fiji', 'tropical', True),
)
CITIES_BY_COUNTRY = {}
for _city in CITIES:
    if _city.country not in COUNTRIES:
        raise ValueError(f'unknown country for {_city.name}')
    CITIES_BY_COUNTRY.setdefault(_city.country, []).append(_city)
CITY_BY_NAME = {c.name: c for c in CITIES}

# Weeks (1-52) in which each climate can host competitive golf, northern hemisphere.
_SEASONS_NORTH = {
    'temperate': range(12, 47), 'oceanic': range(14, 44), 'continental': range(16, 42),
    'mediterranean': range(1, 53), 'subtropical': range(1, 53),
    'tropical': range(1, 53), 'desert': list(range(1, 23)) + list(range(40, 53)), 'alpine': range(24, 37),
}


def season_weeks(city):
    """Set of weeks in which `city` can host competitive golf."""
    weeks = set(_SEASONS_NORTH[city.climate])
    if COUNTRIES[city.country].south and city.climate not in ('tropical', 'desert'):
        weeks = {((w + 25) % 52) + 1 for w in weeks}      # shift by half a year
    return weeks
