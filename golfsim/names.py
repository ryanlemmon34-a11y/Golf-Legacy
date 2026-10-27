"""Fictional golfer names in the right language for every country.

Names are drawn from per-language banks of given names and family names. Some countries mix banks
(South Africa: English and Afrikaans; Malaysia: Malay, Chinese and Indian; Belgium: Dutch and French).
Any full name matching a famous real golfer is rejected, and every name in the world is unique.
Names are shown given-name first everywhere, as golf media do.
"""
from __future__ import annotations

B = {}   # bank name -> (given names, family names)

B['en_us'] = (
    ('James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles', 'Chris',
     'Daniel', 'Matthew', 'Anthony', 'Mark', 'Steven', 'Andrew', 'Josh', 'Kevin', 'Brian', 'Ryan', 'Jacob',
     'Nick', 'Tyler', 'Brandon', 'Kyle', 'Zach', 'Austin', 'Cole', 'Hunter', 'Luke', 'Grant', 'Wyatt', 'Chase',
     'Logan', 'Garrett', 'Brady', 'Tanner', 'Travis', 'Derek', 'Trevor', 'Blake', 'Clay', 'Reed', 'Davis', 'Parker',
     'Carson', 'Jackson', 'Mason', 'Ethan', 'Caleb', 'Owen', 'Landon', 'Connor', 'Sam', 'Ben', 'Max', 'Drew',
     'Wesley', 'Spencer', 'Troy', 'Corey', 'Dustin', 'Brett', 'Jordan', 'Cameron', 'Bryce', 'Trent', 'Gavin',
     'Mitchell', 'Preston', 'Colby', 'Beau', 'Jake', 'Jared', 'Seth', 'Stewart', 'Harrison', 'Tucker', 'Walker'),
    ('Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Miller', 'Davis', 'Wilson', 'Anderson', 'Taylor', 'Moore',
     'Jackson', 'Martin', 'Thompson', 'White', 'Harris', 'Clark', 'Lewis', 'Robinson', 'Walker', 'Hall', 'Allen',
     'Young', 'King', 'Wright', 'Hill', 'Green', 'Adams', 'Baker', 'Nelson', 'Carter', 'Mitchell', 'Roberts',
     'Turner', 'Phillips', 'Campbell', 'Parker', 'Evans', 'Edwards', 'Collins', 'Stewart', 'Morris', 'Murphy',
     'Cook', 'Rogers', 'Morgan', 'Cooper', 'Peterson', 'Bailey', 'Reed', 'Kelly', 'Howard', 'Cox', 'Ward',
     'Richardson', 'Watson', 'Brooks', 'Wood', 'James', 'Bennett', 'Gray', 'Hughes', 'Price', 'Sanders', 'Myers',
     'Long', 'Ross', 'Foster', 'Powell', 'Jenkins', 'Perry', 'Russell', 'Sullivan', 'Bell', 'Coleman', 'Butler',
     'Henderson', 'Barnes', 'Fisher', 'Vaughn', 'Hartley', 'Pruitt', 'Whitaker', 'Caldwell', 'Holloway', 'Pickett',
     'Burnett', 'Dalton', 'Gentry', 'Haskins', 'Lockhart', 'McBride', 'Norwood', 'Ogden', 'Pratt', 'Ramsey',
     'Sheppard', 'Talley', 'Underwood', 'Vance', 'Wheeler', 'Yates', 'Boone', 'Crenshaw', 'Duvall', 'Easley',
     'Fairchild', 'Granger', 'Hensley', 'Kincaid', 'Lyle', 'Mabry', 'Overton', 'Pendleton', 'Quarles', 'Rutledge',
     'Stroud', 'Tillman', 'Upshaw', 'Whitlock', 'Ashby', 'Benton', 'Calloway', 'Dixon', 'Ellison', 'Forsythe'))
B['en_uk'] = (
    ('Oliver', 'Harry', 'George', 'Jack', 'Charlie', 'Thomas', 'James', 'William', 'Alfie', 'Joshua', 'Henry',
     'Freddie', 'Archie', 'Edward', 'Toby', 'Callum', 'Jamie', 'Ross', 'Lewis', 'Matt', 'Tom', 'Ben', 'Sam', 'Dan',
     'Luke', 'Joe', 'Will', 'Ollie', 'Rory', 'Hugo', 'Max', 'Alex', 'Josh', 'Danny', 'Robert', 'Paul', 'Simon',
     'Richard', 'Stuart', 'Gareth', 'Rhys', 'Owain', 'Dylan', 'Aaron', 'Ashley', 'Marcus', 'Nathan', 'Elliot',
     'Jordan', 'Kieran', 'Reece', 'Rupert', 'Felix', 'Barnaby', 'Laurie', 'Ed', 'Jonty', 'Seb'),
    ('Smith', 'Jones', 'Taylor', 'Brown', 'Williams', 'Wilson', 'Johnson', 'Davies', 'Robinson', 'Wright',
     'Thompson', 'Evans', 'Walker', 'White', 'Roberts', 'Green', 'Hall', 'Wood', 'Jackson', 'Clarke', 'Hughes',
     'Edwards', 'Lewis', 'Harrison', 'Turner', 'Hill', 'Cooper', 'Ward', 'Morris', 'Moore', 'Parker', 'Bennett',
     'Carter', 'Shaw', 'Mills', 'Atkinson', 'Fletcher', 'Hargreaves', 'Pickering', 'Whitmore', 'Ashworth',
     'Brierley', 'Cartwright', 'Dobson', 'Entwistle', 'Fairbrother', 'Garside', 'Holroyd', 'Ingham', 'Kershaw',
     'Lomax', 'Marsden', 'Nuttall', 'Oldroyd', 'Pennington', 'Rawlinson', 'Sowerby', 'Thwaite', 'Wainwright',
     'Brackley', 'Cholmondeley', 'Dimmock', 'Fenwick', 'Gillard', 'Hebden', 'Kitching', 'Leadbetter', 'Mottram',
     'Northcott', 'Pettifer', 'Rudd', 'Sumner', 'Tranter', 'Venables', 'Wetherall', 'Yardley', 'Bevan', 'Pryce',
     'Llewellyn', 'Griffiths', 'Prosser', 'Vaughan', 'Rees', 'Powell'))
B['scot'] = (
    ('Callum', 'Ewan', 'Fraser', 'Hamish', 'Iain', 'Angus', 'Calum', 'Euan', 'Finlay', 'Gregor', 'Lachlan',
     'Murray', 'Niall', 'Rory', 'Ruaridh', 'Struan', 'Alasdair', 'Craig', 'Gordon', 'Graeme', 'Kyle', 'Scott',
     'Stuart', 'Ross', 'Jamie', 'Connor', 'Lewis', 'Cameron', 'Douglas', 'Kenneth', 'Malcolm', 'Neil', 'Duncan'),
    ('MacLeod', 'MacDonald', 'Campbell', 'Stewart', 'Robertson', 'Murray', 'Fraser', 'Ross', 'Paterson',
     'Henderson', 'Cameron', 'Sinclair', 'Mackenzie', 'Munro', 'Grant', 'Buchanan', 'Drummond', 'Ferguson',
     'Gillespie', 'Kerr', 'Lindsay', 'Moffat', 'Ogilvie', 'Rennie', 'Shearer', 'Tennant', 'Urquhart', 'Wallace',
     'Baird', 'Crawford', 'Dunbar', 'Galbraith', 'Hendry', 'Imrie', 'Kinnear', 'Laidlaw', 'McAllister', 'McCrae',
     'McInnes', 'McTavish', 'Nairn', 'Pollock', 'Rankin', 'Strachan', 'Thomson', 'Waddell', 'Brodie', 'Cowie'))
B['irish'] = (
    ('Seán', 'Conor', 'Cian', 'Darragh', 'Eoin', 'Fionn', 'Oisín', 'Ronan', 'Niall', 'Ciarán', 'Declan', 'Shane',
     'Brendan', 'Colm', 'Dara', 'Eamon', 'Kevin', 'Liam', 'Padraig', 'Rory', 'Tadhg', 'Aidan', 'Cathal', 'Donal',
     'Fergal', 'Kieran', 'Mark', 'Paul', 'Gavin', 'Stephen', 'Michael', 'Jack', 'Adam', 'Luke'),
    ("O'Brien", "O'Sullivan", 'Murphy', 'Kelly', 'Walsh', 'Byrne', 'Ryan', "O'Connor", "O'Neill", 'Doyle',
     'McCarthy', 'Gallagher', 'Doherty', 'Kennedy', 'Lynch', 'Murray', 'Quinn', 'Moore', 'McLoughlin', 'Carroll',
     'Connolly', 'Daly', 'Dunne', 'Brennan', 'Burke', 'Collins', 'Fitzgerald', 'Hegarty', 'Keane', 'Lenihan',
     'Mulcahy', 'Nolan', 'Phelan', 'Regan', 'Sheehan', 'Tierney', 'Whelan', 'Cullinan', 'Donnelly', 'Flanagan',
     'Hanrahan', 'Kavanagh', 'Maguire', 'McGrath', 'Moran', 'Rafferty', 'Scanlon', 'Brady', 'Corrigan', 'Devlin'))
B['aus'] = (
    ('Jack', 'Lachlan', 'Cooper', 'Riley', 'Mitchell', 'Brodie', 'Jayden', 'Harrison', 'Hamish', 'Angus', 'Bailey',
     'Darcy', 'Fletcher', 'Kane', 'Lincoln', 'Nate', 'Tyson', 'Zac', 'Ben', 'Matt', 'Josh', 'Sam', 'Tom', 'Will',
     'Jake', 'Brad', 'Craig', 'Dean', 'Glen', 'Shane', 'Wade', 'Corey', 'Blake', 'Jarrod', 'Hayden', 'Ryley'),
    ('Smith', 'Jones', 'Williams', 'Brown', 'Wilson', 'Taylor', 'Johnson', 'White', 'Martin', 'Anderson',
     'Thompson', 'Nguyen', 'Thomas', 'Walker', 'Harris', 'Lee', 'Ryan', 'Robinson', 'Kelly', 'King', 'Campbell',
     'Clarke', 'Mitchell', 'Ross', 'Hughes', 'Fraser', 'Gilchrist', 'Hollis', 'Jardine', 'Kingsford', 'Lockyer',
     'McKinnon', 'Noble', 'Paxton', 'Rowley', 'Sutherland', 'Tremayne', 'Varley', 'Whitbread', 'Ashcroft',
     'Bramwell', 'Coburn', 'Dawes', 'Fairweather', 'Gorman', 'Hextall', 'Ingram', 'Kilpatrick', 'Lyons', 'Mayne'))
B['afrikaans'] = (
    ('Johan', 'Pieter', 'Hendrik', 'Jacobus', 'Willem', 'Christo', 'Dewald', 'Francois', 'Gerrit', 'Hennie',
     'Jaco', 'Kobus', 'Louis', 'Morne', 'Neels', 'Riaan', 'Schalk', 'Thinus', 'Wian', 'Zander', 'Ruan', 'Dian',
     'Danie', 'Ernie', 'Fanie', 'Gideon', 'JC', 'Jandre', 'Marnus', 'Retief', 'Stiaan', 'Tertius'),
    ('van der Merwe', 'Botha', 'Pretorius', 'du Plessis', 'van Wyk', 'Nel', 'Fourie', 'Venter', 'Steyn',
     'Coetzee', 'Joubert', 'Kruger', 'le Roux', 'Lombard', 'Marais', 'Naudé', 'Olivier', 'Potgieter', 'Rossouw',
     'Swanepoel', 'Theron', 'Uys', 'Viljoen', 'Wessels', 'Bezuidenhout', 'Cronje', 'de Villiers', 'Erasmus',
     'Grobler', 'Hattingh', 'Jacobs', 'Kotze', 'Labuschagne', 'Meyer', 'Nieuwoudt', 'Oosthuizen', 'Scholtz',
     'Terblanche', 'Vermaak', 'Zondo', 'Mokoena', 'Dlamini', 'Ndlovu', 'Khumalo', 'Mthembu', 'Sithole'))
B['es'] = (
    ('Alejandro', 'Pablo', 'Javier', 'Carlos', 'Sergio', 'Miguel', 'Adrián', 'Jorge', 'Álvaro', 'David', 'Daniel',
     'Diego', 'Gonzalo', 'Iván', 'Jaime', 'Luis', 'Manuel', 'Marcos', 'Mario', 'Nacho', 'Óscar', 'Rafael', 'Raúl',
     'Rubén', 'Santiago', 'Íñigo', 'Unai', 'Borja', 'Eduardo', 'Ángel', 'Alberto', 'Fernando', 'Hugo', 'Nicolás'),
    ('García', 'Fernández', 'González', 'Rodríguez', 'López', 'Martínez', 'Sánchez', 'Pérez', 'Gómez', 'Martín',
     'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno', 'Álvarez', 'Muñoz', 'Romero', 'Alonso', 'Gutiérrez',
     'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Serrano', 'Blanco', 'Molina', 'Morales',
     'Ortega', 'Delgado', 'Castro', 'Ortiz', 'Rubio', 'Marín', 'Sanz', 'Iglesias', 'Medina', 'Garrido', 'Cortés',
     'Castillo', 'Santos', 'Lozano', 'Guerrero', 'Cano', 'Prieto', 'Méndez', 'Calvo', 'Cruz', 'Gallego', 'Vidal',
     'Herrera', 'Peña', 'Arrieta', 'Echeverría', 'Larrañaga', 'Urquiza', 'Zubiri', 'Aguirre', 'Etxeberria'))
B['es_latam'] = (
    ('Juan', 'José', 'Luis', 'Carlos', 'Andrés', 'Mateo', 'Santiago', 'Sebastián', 'Nicolás', 'Felipe', 'Emiliano',
     'Joaquín', 'Tomás', 'Agustín', 'Facundo', 'Franco', 'Ignacio', 'Martín', 'Rodrigo', 'Esteban', 'Gustavo',
     'Ricardo', 'Fabián', 'Mauricio', 'Cristian', 'Julián', 'Lucas', 'Benjamín', 'Maximiliano', 'Gonzalo',
     'Alejandro', 'Diego', 'Emilio', 'Armando', 'Héctor', 'Rafael', 'Vicente', 'Marcelo'),
    ('González', 'Rodríguez', 'Gómez', 'Fernández', 'López', 'Díaz', 'Martínez', 'Pérez', 'García', 'Sánchez',
     'Romero', 'Sosa', 'Álvarez', 'Torres', 'Ruiz', 'Ramírez', 'Flores', 'Acosta', 'Benítez', 'Medina', 'Herrera',
     'Suárez', 'Aguirre', 'Pereyra', 'Gutiérrez', 'Giménez', 'Molina', 'Silva', 'Castro', 'Rojas', 'Ortiz',
     'Núñez', 'Luna', 'Juárez', 'Cabrera', 'Ríos', 'Morales', 'Godoy', 'Vargas', 'Mendoza', 'Ibarra', 'Valdés',
     'Contreras', 'Espinoza', 'Fuentes', 'Carrasco', 'Salazar', 'Ochoa', 'Villalobos', 'Zamora', 'Arango',
     'Restrepo', 'Quintero', 'Echeverri', 'Cárdenas', 'Bustamante', 'Saavedra', 'Figueroa', 'Leiva', 'Paz'))
B['pt'] = (
    ('João', 'Pedro', 'Tiago', 'Miguel', 'Diogo', 'Rui', 'Nuno', 'Ricardo', 'Gonçalo', 'Duarte', 'Francisco',
     'Rafael', 'Bruno', 'Hugo', 'André', 'Luís', 'Gabriel', 'Lucas', 'Matheus', 'Guilherme', 'Felipe', 'Rodrigo',
     'Thiago', 'Vinícius', 'Leonardo', 'Caio', 'Eduardo', 'Fábio', 'Marcelo', 'Henrique'),
    ('Silva', 'Santos', 'Ferreira', 'Pereira', 'Oliveira', 'Costa', 'Rodrigues', 'Martins', 'Jesus', 'Sousa',
     'Fernandes', 'Gonçalves', 'Gomes', 'Lopes', 'Marques', 'Alves', 'Almeida', 'Ribeiro', 'Pinto', 'Carvalho',
     'Teixeira', 'Moreira', 'Correia', 'Mendes', 'Nunes', 'Soares', 'Vieira', 'Monteiro', 'Cardoso', 'Rocha',
     'Barbosa', 'Araújo', 'Cavalcanti', 'Azevedo', 'Brandão', 'Coelho', 'Dias', 'Freitas', 'Macedo', 'Tavares'))
B['fr'] = (
    ('Antoine', 'Baptiste', 'Clément', 'Damien', 'Étienne', 'Florian', 'Grégoire', 'Hugo', 'Julien', 'Louis',
     'Mathieu', 'Nicolas', 'Olivier', 'Pierre', 'Quentin', 'Romain', 'Sébastien', 'Thomas', 'Victor', 'Adrien',
     'Benjamin', 'Cédric', 'Guillaume', 'Jérôme', 'Lucas', 'Maxime', 'Paul', 'Raphaël', 'Théo', 'Yann',
     'Alexandre', 'Arnaud', 'Gaëtan', 'Mathis', 'Valentin'),
    ('Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau', 'Simon',
     'Laurent', 'Lefebvre', 'Michel', 'Garnier', 'Rousseau', 'Fournier', 'Girard', 'Bonnet', 'Dupont', 'Lambert',
     'Fontaine', 'Rousset', 'Chevalier', 'Blanchard', 'Mercier', 'Boyer', 'Gauthier', 'Perrin', 'Morel', 'Leclerc',
     'Marchand', 'Delacroix', 'Beaumont', 'Carré', 'Deschamps', 'Faure', 'Guérin', 'Lacroix', 'Masson', 'Renaud',
     'Vasseur', 'Aubert', 'Brunet', 'Charpentier', 'Duval', 'Hébert', 'Joly', 'Lemaire', 'Picard'))
B['de'] = (
    ('Lukas', 'Maximilian', 'Felix', 'Jonas', 'Leon', 'Paul', 'Niklas', 'Tim', 'Jan', 'Moritz', 'Florian', 'Tobias',
     'Sebastian', 'Matthias', 'Markus', 'Stefan', 'Andreas', 'Christian', 'Philipp', 'Johannes', 'Benedikt',
     'Fabian', 'Dominik', 'Marcel', 'Kai', 'Lars', 'Nico', 'Julian', 'Simon', 'Valentin', 'Bernd', 'Jürgen'),
    ('Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner', 'Becker', 'Schulz', 'Hoffmann',
     'Schäfer', 'Koch', 'Bauer', 'Richter', 'Klein', 'Wolf', 'Schröder', 'Neumann', 'Schwarz', 'Zimmermann',
     'Braun', 'Krüger', 'Hofmann', 'Hartmann', 'Lange', 'Schmitt', 'Werner', 'Krause', 'Meier', 'Lehmann',
     'Huber', 'Gruber', 'Steiner', 'Moser', 'Brunner', 'Egger', 'Hofer', 'Leitner', 'Baumgartner', 'Keller',
     'Frei', 'Gerber', 'Kaufmann', 'Vogt', 'Ammann', 'Bachmann', 'Eberhardt', 'Falkenberg', 'Gottschalk'))
B['nl'] = (
    ('Daan', 'Sem', 'Lucas', 'Milan', 'Levi', 'Bram', 'Thijs', 'Jesse', 'Ruben', 'Stijn', 'Joost', 'Pieter',
     'Wouter', 'Sander', 'Niels', 'Bas', 'Koen', 'Jeroen', 'Floris', 'Maarten', 'Tijmen', 'Wim', 'Rik', 'Dries',
     'Pieterjan', 'Arnout', 'Lander', 'Wout', 'Jelle', 'Siebe'),
    ('de Jong', 'Jansen', 'de Vries', 'van den Berg', 'van Dijk', 'Bakker', 'Janssen', 'Visser', 'Smit',
     'Meijer', 'de Boer', 'Mulder', 'de Groot', 'Bos', 'Vos', 'Peters', 'Hendriks', 'van Leeuwen', 'Dekker',
     'Brouwer', 'de Wit', 'Dijkstra', 'Smits', 'de Graaf', 'van der Linden', 'Kok', 'Jacobs', 'Peeters', 'Maes',
     'Claes', 'Goossens', 'Wouters', 'De Smet', 'Willems', 'Verhoeven', 'Van Damme', 'Lemmens', 'Vermeulen'))
B['sv'] = (
    ('Erik', 'Lars', 'Karl', 'Anders', 'Johan', 'Per', 'Nils', 'Lukas', 'Oscar', 'William', 'Elias', 'Hugo',
     'Axel', 'Linus', 'Viktor', 'Gustav', 'Albin', 'Filip', 'Emil', 'Jesper', 'Mattias', 'Henrik', 'Fredrik',
     'Rasmus', 'Sebastian', 'Ludvig', 'Alfred', 'Adam', 'Isak', 'Jonatan'),
    ('Andersson', 'Johansson', 'Karlsson', 'Nilsson', 'Eriksson', 'Larsson', 'Olsson', 'Persson', 'Svensson',
     'Gustafsson', 'Pettersson', 'Jonsson', 'Jansson', 'Hansson', 'Bengtsson', 'Lindberg', 'Lindqvist', 'Lindgren',
     'Berglund', 'Fredriksson', 'Sandberg', 'Henriksson', 'Forsberg', 'Sjöberg', 'Wallin', 'Engström', 'Eklund',
     'Danielsson', 'Lundin', 'Håkansson', 'Björk', 'Bergström', 'Holmberg', 'Nyström', 'Strand', 'Ekström'))
B['da'] = (
    ('Mads', 'Rasmus', 'Mikkel', 'Frederik', 'Mathias', 'Jonas', 'Oliver', 'Magnus', 'Christian', 'Søren',
     'Anders', 'Jesper', 'Thomas', 'Nicolai', 'Kasper', 'Emil', 'Lasse', 'Thorbjørn', 'Rune', 'Esben', 'Asger'),
    ('Nielsen', 'Jensen', 'Hansen', 'Pedersen', 'Andersen', 'Christensen', 'Larsen', 'Sørensen', 'Rasmussen',
     'Jørgensen', 'Petersen', 'Madsen', 'Kristensen', 'Olsen', 'Thomsen', 'Christiansen', 'Poulsen', 'Johansen',
     'Møller', 'Mortensen', 'Bach', 'Dahl', 'Holm', 'Lund', 'Skov', 'Vestergaard', 'Kjær', 'Bang', 'Juul'))
B['no'] = (
    ('Ole', 'Magnus', 'Henrik', 'Jakob', 'Sander', 'Tobias', 'Martin', 'Even', 'Sindre', 'Eirik', 'Kristian',
     'Håkon', 'Vegard', 'Espen', 'Andreas', 'Torbjørn', 'Kristoffer', 'Aksel', 'Mats', 'Stian'),
    ('Hansen', 'Johansen', 'Olsen', 'Larsen', 'Andersen', 'Pedersen', 'Nilsen', 'Kristiansen', 'Jensen', 'Karlsen',
     'Haugen', 'Bakken', 'Solberg', 'Strand', 'Moe', 'Lie', 'Berg', 'Hagen', 'Dahl', 'Eide', 'Halvorsen', 'Aune'))
B['fi'] = (
    ('Mikko', 'Juha', 'Antti', 'Jani', 'Sami', 'Ville', 'Tuomas', 'Lauri', 'Eero', 'Aleksi', 'Onni', 'Elias',
     'Joonas', 'Kalle', 'Teemu', 'Veeti', 'Kristian', 'Oskari'),
    ('Korhonen', 'Virtanen', 'Mäkinen', 'Nieminen', 'Mäkelä', 'Hämäläinen', 'Laine', 'Heikkinen', 'Koskinen',
     'Järvinen', 'Lehtonen', 'Lehtinen', 'Saarinen', 'Salminen', 'Heinonen', 'Niemi', 'Kinnunen', 'Salonen'))
B['it'] = (
    ('Francesco', 'Alessandro', 'Lorenzo', 'Matteo', 'Andrea', 'Gabriele', 'Leonardo', 'Riccardo', 'Tommaso',
     'Edoardo', 'Federico', 'Giovanni', 'Luca', 'Marco', 'Nicolò', 'Pietro', 'Stefano', 'Davide', 'Filippo',
     'Guido', 'Renato', 'Emanuele', 'Giacomo', 'Michele'),
    ('Rossi', 'Russo', 'Ferrari', 'Esposito', 'Bianchi', 'Romano', 'Colombo', 'Ricci', 'Marino', 'Greco', 'Bruno',
     'Gallo', 'Conti', 'De Luca', 'Mancini', 'Costa', 'Giordano', 'Rizzo', 'Lombardi', 'Moretti', 'Barbieri',
     'Fontana', 'Santoro', 'Mariani', 'Rinaldi', 'Caruso', 'Ferrara', 'Galli', 'Martini', 'Leone', 'Gentile'))
B['cs'] = (
    ('Jakub', 'Jan', 'Tomáš', 'Matěj', 'Ondřej', 'Vojtěch', 'Petr', 'Lukáš', 'Martin', 'Filip', 'David', 'Adam'),
    ('Novák', 'Svoboda', 'Novotný', 'Dvořák', 'Černý', 'Procházka', 'Kučera', 'Veselý', 'Horák', 'Němec',
     'Marek', 'Pospíšil', 'Hájek', 'Král', 'Jelínek'))
B['pl'] = (
    ('Jakub', 'Kacper', 'Szymon', 'Mateusz', 'Bartosz', 'Michał', 'Piotr', 'Krzysztof', 'Tomasz', 'Paweł',
     'Wojciech', 'Adrian'),
    ('Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński', 'Lewandowski', 'Zieliński',
     'Szymański', 'Woźniak', 'Dąbrowski', 'Kozłowski', 'Jankowski', 'Mazur'))
B['tr'] = (
    ('Mehmet', 'Mustafa', 'Ahmet', 'Emre', 'Burak', 'Can', 'Cem', 'Deniz', 'Kerem', 'Mert', 'Ozan', 'Tolga',
     'Yusuf', 'Arda'),
    ('Yılmaz', 'Kaya', 'Demir', 'Şahin', 'Çelik', 'Yıldız', 'Yıldırım', 'Öztürk', 'Aydın', 'Özdemir', 'Arslan',
     'Doğan', 'Kılıç', 'Aslan'))
B['ar'] = (
    ('Ahmed', 'Mohammed', 'Omar', 'Ali', 'Khalid', 'Yousef', 'Hamad', 'Saeed', 'Rashid', 'Faisal', 'Sultan',
     'Abdullah', 'Hassan', 'Karim', 'Tariq', 'Nasser', 'Majid', 'Adel', 'Ziad', 'Mahmoud', 'Amr', 'Youssef',
     'Mehdi', 'Ayoub', 'Hamza', 'Ismail'),
    ('Al Mansouri', 'Al Hashimi', 'Al Suwaidi', 'Al Nuaimi', 'Al Thani', 'Al Kuwari', 'Al Ghamdi', 'Al Harbi',
     'Al Otaibi', 'Al Zahrani', 'Al Balushi', 'Al Habsi', 'Al Khalifa', 'Hassan', 'Ibrahim', 'Mahmoud', 'Mostafa',
     'Abdelrahman', 'El Sayed', 'Fathy', 'Bennani', 'El Amrani', 'Alaoui', 'Benjelloun', 'Tazi', 'Idrissi',
     'Chraibi', 'Berrada', 'Lahlou', 'Fassi'))
B['east_africa'] = (
    ('Brian', 'David', 'Dennis', 'Eric', 'Felix', 'George', 'Isaac', 'James', 'John', 'Joseph', 'Kevin', 'Peter',
     'Samuel', 'Simon', 'Stephen', 'Tony', 'Victor', 'Collins', 'Dismas', 'Greg', 'Mutahi', 'Njoroge', 'Kibet',
     'Tendai', 'Tafadzwa', 'Farai', 'Chipo', 'Mwila', 'Bwalya', 'Tatenda'),
    ('Kamau', 'Mwangi', 'Otieno', 'Ochieng', 'Kiprono', 'Wanjiru', 'Njoroge', 'Odhiambo', 'Kariuki', 'Maina',
     'Ndungu', 'Wekesa', 'Chege', 'Moyo', 'Ncube', 'Dube', 'Sibanda', 'Chikwanha', 'Mutasa', 'Banda', 'Phiri',
     'Mulenga', 'Tembo', 'Zulu', 'Mwale', 'Shikongo', 'Nghipondoka', 'Amupolo', 'Hamutenya', 'Iyambo'))
B['ng'] = (
    ('Chinedu', 'Emeka', 'Oluwaseun', 'Tunde', 'Babatunde', 'Ifeanyi', 'Chukwuemeka', 'Femi', 'Segun', 'Uche',
     'Kelechi', 'Obinna', 'Ayodele', 'Damilola', 'Tobi'),
    ('Okafor', 'Adeyemi', 'Okonkwo', 'Balogun', 'Eze', 'Nwosu', 'Adebayo', 'Ogunleye', 'Ibekwe', 'Onyeka',
     'Abubakar', 'Bello', 'Danjuma', 'Afolabi', 'Oyelaran'))
B['jp'] = (
    ('Hiroshi', 'Takashi', 'Kenji', 'Yuki', 'Daiki', 'Haruto', 'Ren', 'Sota', 'Yuto', 'Kaito', 'Riku', 'Shota',
     'Ryo', 'Kazuki', 'Tomoya', 'Yusaku', 'Naoki', 'Takumi', 'Shun', 'Kota', 'Taiga', 'Hayato', 'Keita', 'Masaki',
     'Ryosuke', 'Satoshi', 'Shingo', 'Tatsuya', 'Yosuke', 'Akira', 'Daisuke', 'Genki', 'Hiroki', 'Kosuke'),
    ('Sato', 'Suzuki', 'Takahashi', 'Tanaka', 'Watanabe', 'Ito', 'Yamamoto', 'Nakamura', 'Kobayashi', 'Kato',
     'Yoshida', 'Yamada', 'Sasaki', 'Yamaguchi', 'Matsumoto', 'Inoue', 'Kimura', 'Hayashi', 'Shimizu', 'Yamazaki',
     'Mori', 'Abe', 'Ikeda', 'Hashimoto', 'Yamashita', 'Ishikawa', 'Nakajima', 'Maeda', 'Fujita', 'Ogawa',
     'Goto', 'Okada', 'Hasegawa', 'Murakami', 'Kondo', 'Ishii', 'Saito', 'Sakamoto', 'Endo', 'Aoki', 'Fujii',
     'Nishimura', 'Fukuda', 'Ota', 'Miura', 'Okamoto', 'Matsuda', 'Nakagawa', 'Harada', 'Takeda'))
B['kr'] = (
    ('Min-jun', 'Seo-jun', 'Do-yun', 'Ji-ho', 'Joon-young', 'Hyun-woo', 'Sung-min', 'Jae-won', 'Dong-hyun',
     'Tae-hoon', 'Woo-jin', 'Seung-ho', 'Ji-hoon', 'Young-soo', 'Kyung-tae', 'Sang-hyun', 'Han-sol', 'Jun-seo',
     'Ye-chan', 'Si-hyun', 'Gun-woo', 'Hyeon-jun', 'In-ho', 'Byung-chul', 'Chang-min', 'Dae-ho', 'Eun-sung'),
    ('Kim', 'Lee', 'Park', 'Choi', 'Jung', 'Kang', 'Cho', 'Yoon', 'Jang', 'Lim', 'Han', 'Oh', 'Seo', 'Shin',
     'Kwon', 'Hwang', 'Ahn', 'Song', 'Yoo', 'Hong', 'Jeon', 'Ko', 'Moon', 'Yang', 'Son', 'Baek', 'Heo', 'Nam'))
B['zh'] = (
    ('Wei', 'Jun', 'Hao', 'Yu', 'Jian', 'Ming', 'Lei', 'Tao', 'Yang', 'Chen', 'Zhi', 'Long', 'Bo', 'Kai', 'Xin',
     'Jie', 'Peng', 'Rui', 'Hui', 'Feng', 'Zihan', 'Haoran', 'Yichen', 'Zhiwei', 'Jiahao', 'Tianyu', 'Junjie',
     'Zhenyu', 'Mingyu', 'Shuai', 'Yifan'),
    ('Wang', 'Li', 'Zhang', 'Liu', 'Chen', 'Yang', 'Huang', 'Zhao', 'Wu', 'Zhou', 'Xu', 'Sun', 'Ma', 'Zhu', 'Hu',
     'Guo', 'He', 'Gao', 'Lin', 'Luo', 'Zheng', 'Liang', 'Xie', 'Song', 'Tang', 'Han', 'Feng', 'Deng', 'Cao'))
B['tw'] = (
    ('Chun-hao', 'Wei-lun', 'Yu-cheng', 'Kuan-ting', 'Po-yu', 'Chih-hao', 'Tsung-han', 'Yi-hsuan', 'Chia-wei',
     'Cheng-tsung', 'Hung-lin', 'Kai-jen', 'Ming-hsun', 'Shih-chang', 'Wen-yi', 'Yen-ting'),
    ('Chen', 'Lin', 'Huang', 'Chang', 'Lee', 'Wang', 'Wu', 'Liu', 'Tsai', 'Yang', 'Hsu', 'Cheng', 'Hsieh', 'Kuo',
     'Lai', 'Chiang', 'Yeh', 'Chou', 'Lu', 'Pan'))
B['in'] = (
    ('Arjun', 'Rohan', 'Vikram', 'Aditya', 'Karan', 'Rahul', 'Siddharth', 'Aarav', 'Vihaan', 'Ishaan', 'Kabir',
     'Shubhankar', 'Gaganjeet', 'Jeev', 'Rashid', 'Anirban', 'Udayan', 'Manav', 'Yuvraj', 'Ajeetesh', 'Honey',
     'Khalin', 'Viraj', 'Om', 'Sachin', 'Harendra', 'Aryan', 'Dev'),
    ('Sharma', 'Singh', 'Kumar', 'Patel', 'Gupta', 'Reddy', 'Iyer', 'Nair', 'Menon', 'Chopra', 'Malhotra',
     'Kapoor', 'Mehta', 'Joshi', 'Rao', 'Bhatia', 'Sandhu', 'Gill', 'Bhullar', 'Dhillon', 'Chawla', 'Saini',
     'Thakur', 'Verma', 'Pillai', 'Banerjee', 'Chatterjee', 'Das', 'Bose', 'Mukherjee'))
B['th'] = (
    ('Somchai', 'Kittipong', 'Anan', 'Prayad', 'Thongchai', 'Panuphol', 'Sadom', 'Chanachok', 'Phachara',
     'Kiradech', 'Natthapong', 'Jazz', 'Poom', 'Danthai', 'Itthipat', 'Rattanon', 'Sarit', 'Tirawat', 'Wanchai',
     'Pavit', 'Suradit', 'Atiruj'),
    ('Srisuk', 'Wongsawat', 'Chaiyaporn', 'Kaewkanjana', 'Boonma', 'Sukcharoen', 'Rattanakul', 'Thammasak',
     'Suwannarat', 'Prasertsuk', 'Jaidee', 'Nitithorn', 'Phromsuk', 'Saengchai', 'Kongkaew', 'Wattanasin',
     'Chantarasiri', 'Pongpanit', 'Sirikul', 'Tangsakul', 'Yodsuwan', 'Charoensuk'))
B['my'] = (
    ('Ahmad', 'Muhammad', 'Amir', 'Danial', 'Haziq', 'Iskandar', 'Syafiq', 'Faiz', 'Arif', 'Gavin', 'Kok Wei',
     'Jun Hao', 'Wei Jie', 'Ravi', 'Suresh', 'Nicholas', 'Rizal', 'Azhar', 'Galven'),
    ('Abdullah', 'Rahman', 'Ismail', 'Ibrahim', 'Hashim', 'Yusof', 'Tan', 'Lim', 'Lee', 'Ng', 'Wong', 'Chan',
     'Teh', 'Ong', 'Krishnan', 'Raj', 'Subramaniam', 'Green', 'Fernandez'))
B['id'] = (
    ('Budi', 'Agus', 'Rizky', 'Dimas', 'Fajar', 'Galih', 'Hendra', 'Iqbal', 'Joko', 'Kevin', 'Naraajie',
     'Rory', 'Danny', 'George', 'Benny'),
    ('Santoso', 'Wijaya', 'Kusuma', 'Pratama', 'Saputra', 'Hidayat', 'Nugroho', 'Setiawan', 'Gunawan',
     'Susanto', 'Halim', 'Tanoto', 'Hartono', 'Sutanto'))
B['vi'] = (
    ('Minh', 'Duc', 'Huy', 'Khoa', 'Long', 'Nam', 'Phong', 'Quang', 'Thanh', 'Trung', 'Tuan', 'Bao', 'Hieu',
     'Khanh', 'Vinh'),
    ('Nguyen', 'Tran', 'Le', 'Pham', 'Hoang', 'Huynh', 'Phan', 'Vu', 'Vo', 'Dang', 'Bui', 'Do', 'Ho', 'Ngo'))
B['ph'] = (
    ('Juan', 'Miguel', 'Angelo', 'Paolo', 'Carlo', 'Rico', 'Jerome', 'Mark', 'Kevin', 'Joshua', 'Justin', 'Rhenzo',
     'Clyde', 'Aidric', 'Jhonnel', 'Tony', 'Elmer'),
    ('Santos', 'Reyes', 'Cruz', 'Bautista', 'Ocampo', 'Garcia', 'Mendoza', 'Torres', 'Tomas', 'Andrada',
     'Villanueva', 'Ramos', 'Castillo', 'Aquino', 'Dizon', 'Navarro', 'Que', 'Pagunsan', 'Lascuña'))
B['fj'] = (
    ('Vijay', 'Ravi', 'Sanjay', 'Josefa', 'Isikeli', 'Sakiusa', 'Tevita', 'Ratu', 'Peni', 'Akuila'),
    ('Prasad', 'Chand', 'Kumar', 'Naidu', 'Lal', 'Naivalu', 'Tuilagi', 'Ravouvou', 'Qarase', 'Waqa'))
B['mu'] = (
    ('Jean', 'Kevin', 'Yannick', 'Ravi', 'Ashwin', 'Nitin', 'Louis', 'Christophe', 'Arvind', 'Steeve'),
    ('Ramdin', 'Seebaluck', 'Lagesse', 'Desvaux', 'Jhugroo', 'Boodhoo', 'Ramgoolam', 'Lebon', 'Maurel', 'Rose'))

# Countries -> (bank, weight) mixes
NATION_BANKS = {
    'USA': (('en_us', 1.0),), 'Canada': (('en_us', .85), ('fr', .15)), 'Mexico': (('es_latam', 1.0),),
    'Brazil': (('pt', .9), ('it', .05), ('de', .05)), 'Argentina': (('es_latam', .8), ('it', .2)),
    'Chile': (('es_latam', 1.0),), 'Colombia': (('es_latam', 1.0),), 'Peru': (('es_latam', 1.0),),
    'England': (('en_uk', 1.0),), 'Scotland': (('scot', .8), ('en_uk', .2)), 'Wales': (('en_uk', 1.0),),
    'Ireland': (('irish', 1.0),), 'Northern Ireland': (('irish', .6), ('scot', .2), ('en_uk', .2)),
    'Spain': (('es', 1.0),), 'Portugal': (('pt', 1.0),), 'France': (('fr', 1.0),), 'Germany': (('de', 1.0),),
    'Austria': (('de', 1.0),), 'Switzerland': (('de', .7), ('fr', .2), ('it', .1)), 'Netherlands': (('nl', 1.0),),
    'Belgium': (('nl', .6), ('fr', .4)), 'Denmark': (('da', 1.0),), 'Sweden': (('sv', 1.0),), 'Norway': (('no', 1.0),),
    'Finland': (('fi', 1.0),), 'Italy': (('it', 1.0),), 'Czechia': (('cs', 1.0),), 'Poland': (('pl', 1.0),),
    'Turkey': (('tr', 1.0),), 'United Arab Emirates': (('ar', 1.0),), 'Qatar': (('ar', 1.0),),
    'Saudi Arabia': (('ar', 1.0),), 'Bahrain': (('ar', 1.0),), 'Oman': (('ar', 1.0),), 'Egypt': (('ar', 1.0),),
    'Morocco': (('ar', .8), ('fr', .2)), 'South Africa': (('en_uk', .35), ('afrikaans', .65)),
    'Kenya': (('east_africa', 1.0),), 'Nigeria': (('ng', 1.0),), 'Zimbabwe': (('east_africa', .7), ('en_uk', .3)),
    'Namibia': (('afrikaans', .5), ('east_africa', .5)), 'Zambia': (('east_africa', 1.0),),
    'Mauritius': (('mu', 1.0),), 'Japan': (('jp', 1.0),), 'South Korea': (('kr', 1.0),), 'China': (('zh', 1.0),),
    'Taiwan': (('tw', 1.0),), 'India': (('in', 1.0),), 'Thailand': (('th', 1.0),), 'Malaysia': (('my', 1.0),),
    'Singapore': (('my', .5), ('zh', .5)), 'Philippines': (('ph', 1.0),), 'Indonesia': (('id', 1.0),),
    'Vietnam': (('vi', 1.0),), 'Australia': (('aus', .8), ('en_uk', .2)), 'New Zealand': (('aus', .8), ('en_uk', .2)),
    'Fiji': (('fj', 1.0),),
}

# Famous real golfers (past and present): no generated golfer may share one of these names.
FAMOUS = frozenset(n.lower() for n in (
    'Tiger Woods', 'Jack Nicklaus', 'Arnold Palmer', 'Gary Player', 'Ben Hogan', 'Sam Snead', 'Bobby Jones',
    'Tom Watson', 'Lee Trevino', 'Seve Ballesteros', 'Nick Faldo', 'Greg Norman', 'Phil Mickelson', 'Rory McIlroy',
    'Scottie Scheffler', 'Jon Rahm', 'Brooks Koepka', 'Dustin Johnson', 'Jordan Spieth', 'Justin Thomas',
    'Xander Schauffele', 'Collin Morikawa', 'Viktor Hovland', 'Ludvig Aberg', 'Ludvig Åberg', 'Tommy Fleetwood',
    'Shane Lowry', 'Patrick Cantlay', 'Bryson DeChambeau', 'Hideki Matsuyama', 'Adam Scott', 'Jason Day',
    'Cameron Smith', 'Justin Rose', 'Paul Casey', 'Ian Poulter', 'Lee Westwood', 'Luke Donald', 'Sergio Garcia',
    'Sergio García', 'Henrik Stenson', 'Padraig Harrington', 'Pádraig Harrington', 'Graeme McDowell',
    'Darren Clarke', 'Ernie Els', 'Retief Goosen', 'Louis Oosthuizen', 'Charl Schwartzel', 'Trevor Immelman',
    'Vijay Singh', 'Fred Couples', 'Davis Love', 'Payne Stewart', 'Hale Irwin', 'Ray Floyd', 'Raymond Floyd',
    'Johnny Miller', 'Tom Kite', 'Curtis Strange', 'Corey Pavin', 'Mark O\'Meara', 'Fuzzy Zoeller', 'Craig Stadler',
    'Zach Johnson', 'Bubba Watson', 'Matt Kuchar', 'Rickie Fowler', 'Webb Simpson', 'Jim Furyk', 'Stewart Cink',
    'Kevin Kisner', 'Tony Finau', 'Max Homa', 'Sam Burns', 'Wyndham Clark', 'Brian Harman', 'Keegan Bradley',
    'Jason Dufner', 'Gary Woodland', 'Patrick Reed', 'Jimmy Walker', 'Danny Willett', 'Matt Fitzpatrick',
    'Tyrrell Hatton', 'Robert MacIntyre', 'Bob MacIntyre', 'Sepp Straka', 'Tom Kim', 'Si Woo Kim', 'Sungjae Im',
    'Byeong Hun An', 'K.J. Choi', 'Y.E. Yang', 'Min Woo Lee', 'Ryo Ishikawa', 'Keita Nakajima', 'Shingo Katayama',
    'Isao Aoki', 'Jumbo Ozaki', 'Masashi Ozaki', 'Kiradech Aphibarnrat', 'Jazz Janewattananond', 'Thongchai Jaidee',
    'Anirban Lahiri', 'Shubhankar Sharma', 'Jeev Milkha Singh', 'Arjun Atwal', 'Gaganjeet Bhullar',
    'Joaquin Niemann', 'Joaquín Niemann', 'Mito Pereira', 'Abraham Ancer', 'Carlos Ortiz', 'Camilo Villegas',
    'Angel Cabrera', 'Ángel Cabrera', 'Emiliano Grillo', 'Andres Romero', 'Eduardo Romero', 'Roberto De Vicenzo',
    'Nicolas Colsaerts', 'Thomas Pieters', 'Thomas Detry', 'Victor Perez', 'Victor Dubuisson', 'Matthieu Pavon',
    'Martin Kaymer', 'Bernhard Langer', 'Stephan Jaeger', 'Alex Noren', 'Alex Norén', 'Jesper Parnevik',
    'Robert Karlsson', 'Thomas Bjorn', 'Thomas Bjørn', 'Rasmus Hojgaard', 'Nicolai Hojgaard', 'Søren Kjeldsen',
    'Thorbjorn Olesen', 'Thorbjørn Olesen', 'Lucas Bjerregaard', 'Kristoffer Ventura', 'Mikko Ilonen',
    'Sami Valimaki', 'Francesco Molinari', 'Edoardo Molinari', 'Guido Migliozzi', 'Costantino Rocca',
    'Miguel Angel Jimenez', 'Miguel Ángel Jiménez', 'Jose Maria Olazabal', 'José María Olazábal', 'Rafa Cabrera Bello',
    'Adrian Otaegui', 'Pablo Larrazabal', 'Pablo Larrazábal', 'Jorge Campillo', 'Ewen Ferguson', 'Colin Montgomerie',
    'Sandy Lyle', 'Paul Lawrie', 'Russell Knox', 'Stephen Gallacher', 'Martin Laird', 'Seamus Power',
    'Tom McKibbin', 'Ian Woosnam', 'Jamie Donaldson', 'Phil Price', 'Steve Elkington', 'Peter Thomson',
    'Ian Baker-Finch', 'Geoff Ogilvy', 'Aaron Baddeley', 'Marc Leishman', 'Lucas Herbert', 'Cam Davis',
    'Ryan Fox', 'Michael Campbell', 'Bob Charles', 'Danny Lee', 'Nick Price', 'Mark McNulty', 'Brendon de Jonge',
    'Christiaan Bezuidenhout', 'Dean Burmester', 'Thriston Lawrence', 'Branden Grace', 'Garrick Higgo',
    'Erik van Rooyen', 'Tim Clark', 'Rory Sabbatini', 'Joost Luiten', 'Haotong Li', 'Li Haotong', 'Zhang Xinjun',
    'Wu Ashun', 'C.T. Pan', 'Kevin Yu', 'Mackenzie Hughes', 'Corey Conners', 'Adam Hadwin', 'Nick Taylor',
    'Mike Weir', 'Taylor Pendrith', 'Hideto Tanihara', 'Hiroshi Iwata', 'Shigeki Maruyama', 'Kazuhiro Yamashita',
    'Satoshi Kodaira', 'Takumi Kanaya', 'Ryo Hisatsune', 'Gary Nicklaus', 'Bill Haas', 'Jay Haas', 'Hunter Mahan',
    'Lucas Glover', 'Chris Kirk', 'Russell Henley', 'Harris English', 'Billy Horschel', 'Cameron Young',
    'Will Zalatoris', 'Sahith Theegala', 'Akshay Bhatia', 'Tom Hoge', 'Denny McCarthy', 'Nick Dunlap',
    'Gordon Sargent', 'Michael Thorbjornsen', 'Neal Shipley', 'Sam Bennett', 'Chris Gotterup', 'Davis Thompson',
    'Ben Griffin', 'J.J. Spaun', 'Taylor Moore', 'Eric Cole', 'Justin Lower', 'Adam Schenk', 'Andrew Putnam',
    'Kevin Streelman', 'Brendan Steele', 'Charley Hoffman', 'Kevin Na', 'Jason Kokrak', 'Talor Gooch',
    'Peter Uihlein', 'Pat Perez', 'Charles Howell', 'Ryan Moore', 'Ryan Palmer', 'Kyle Stanley', 'Brian Gay',
    'Tom Lehman', 'David Duval', 'Justin Leonard', 'Mark Calcavecchia', 'Steve Stricker', 'Kenny Perry',
    'John Daly', 'Rocco Mediate', 'Chris DiMarco', 'Chad Campbell', 'Ben Crenshaw', 'Larry Nelson',
    'Lanny Wadkins', 'Hal Sutton', 'Bob Tway', 'Paul Azinger', 'Jeff Sluman', 'Mark Brooks', 'Rich Beem',
    'Shaun Micheel', 'Todd Hamilton', 'Ben Curtis', 'Michael Kim', 'John Smith', 'James Smith', 'David Smith',
    'Tom Smith', 'Rory Murphy', 'Liam Kelly', 'Tom Lewis', 'David Lynn', 'Paul Dunne', 'Joe Carr', 'Harry Vardon',
    'James Braid', 'J.H. Taylor', 'Walter Hagen', 'Gene Sarazen', 'Byron Nelson', 'Tommy Armour', 'Old Tom Morris',
    'Young Tom Morris', 'Tom Morris', 'Willie Park', 'Kel Nagle', 'Billy Casper', 'Julius Boros', 'Ken Venturi',
    'Gene Littler', 'Tony Jacklin', 'Bob Charles', 'Roberto de Vicenzo', 'Chi Chi Rodriguez', 'Bernd Wiesberger',
    'Matthias Schwab', 'Yannik Paul', 'Jeremy Paul', 'Max Kieffer', 'Marcel Siem', 'Alexander Levy',
    'Romain Langasque', 'Antoine Rozner', 'Adrien Saddier', 'Clement Sordet', 'Julien Guerrier', 'Gregory Havret',
    'Thomas Levet', 'Jean van de Velde', 'Jose Coceres', 'Fabian Gomez', 'Julian Etulain', 'Alejandro Tosti',
    'Santiago Tarrio', 'Joaquin Niemann', 'Felipe Aguilar', 'Guillermo Mito Pereira', 'Sebastian Munoz',
    'Sebastián Muñoz', 'Nico Echavarria', 'Nicolás Echavarría', 'Marcelo Rozo', 'Juan Sebastian Munoz',
    'Adilson da Silva', 'Alexandre Rocha', 'Jhonattan Vegas', 'Fernando Valenzuela', 'Rafael Nadal'))


def make_name(country, rng, taken):
    """A unique fictional name for a golfer from `country` (`taken`: names already in the world)."""
    mix = NATION_BANKS[country]
    for _ in range(500):
        bank = rng.choices([b for b, _ in mix], [w for _, w in mix])[0]
        given, family = B[bank]
        name = f'{rng.choice(given)} {rng.choice(family)}'
        if name.lower() not in FAMOUS and name not in taken:
            taken.add(name)
            return name
    # Large countries can run short: add a middle initial (as real tour players do).
    for _ in range(2000):
        bank = rng.choices([b for b, _ in mix], [w for _, w in mix])[0]
        given, family = B[bank]
        name = f'{rng.choice(given)} {chr(65 + rng.randrange(26))}. {rng.choice(family)}'
        if name not in taken:
            taken.add(name)
            return name
    raise RuntimeError(f'could not name a golfer from {country}')
