"""Fictional golfer names in the right language for every country.

Names are drawn from per-language banks of given names and family names. Some countries mix banks
(South Africa: English and Afrikaans; Malaysia: Malay, Chinese and Indian; Belgium: Dutch and French).
Any full name matching a famous real golfer is rejected, and no two people active at the same time share a
name (careers.names_in_use: a retired person's name can recur in a later generation).
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


# More names for the banks the largest golfing nations draw on (2090 world audit: by 2089 three in four
# names carried a middle initial because these ran short). Used for people who arrive after a world began
# (make_name with `in_use`), so a seed's starting world keeps exactly the names it always had.
EXTRA = {
    'en_us': (
        ('Aiden', 'Bennett', 'Brooks', 'Camden', 'Carter', 'Chandler', 'Christian', 'Clayton', 'Colton', 'Dalton',
         'Dawson', 'Dillon', 'Easton', 'Eli', 'Elliott', 'Emmett', 'Evan', 'Finn', 'Garrison', 'Graham', 'Grayson',
         'Griffin', 'Hayes', 'Holden', 'Hudson', 'Isaac', 'Jace', 'Jalen', 'Jameson', 'Jonah', 'Keaton', 'Lane',
         'Levi', 'Lucas', 'Marshall', 'Miles', 'Nolan', 'Noah', 'Pierce', 'Quinn', 'Reid', 'Rhett', 'Sawyer',
         'Silas', 'Tate', 'Weston', 'Zane', 'Marcus', 'Terrell', 'Darius', 'Andre', 'Malik', 'Isaiah', 'Elijah',
         'Gabriel', 'Adrian', 'Mateo', 'Julian', 'Victor', 'Andres', 'Rafael', 'Xavier', 'Dominic', 'Jasper'),
        ('Abbott', 'Atkins', 'Ballard', 'Barrett', 'Beckett', 'Blackwell', 'Bowman', 'Bradford', 'Brennan', 'Burke',
         'Carlisle', 'Chambers', 'Cline', 'Conway', 'Crawford', 'Cross', 'Cunningham', 'Delaney', 'Dennison',
         'Donovan', 'Dougherty', 'Drake', 'Ellington', 'Emerson', 'Farrell', 'Fitzpatrick', 'Fleming', 'Gibbs',
         'Goodwin', 'Graves', 'Griffith', 'Hale', 'Hammond', 'Hardin', 'Harmon', 'Hartman', 'Hawkins', 'Hendricks',
         'Holt', 'Hopkins', 'Huffman', 'Ingram', 'Jennings', 'Keller', 'Kendrick', 'Kirby', 'Lambert', 'Larkin',
         'Lawson', 'Lowery', 'Maddox', 'Malone', 'Mann', 'Marsh', 'McAllister', 'McCoy', 'McDaniel', 'Mercer',
         'Merritt', 'Monroe', 'Nash', 'Newman', 'Nichols', 'Norris', 'Oakley', 'Osborne', 'Pace', 'Patton',
         'Prescott', 'Randall', 'Reese', 'Rhodes', 'Rivers', 'Rollins', 'Salazar', 'Shelton', 'Sherwood',
         'Slater', 'Stafford', 'Stanton', 'Sterling', 'Sutton', 'Thornton', 'Townsend', 'Walton', 'Warner',
         'Webster', 'Whitfield', 'Wilder', 'Winslow', 'Wolfe', 'Woodard', 'Washington', 'Jefferson', 'Banks',
         'Freeman', 'Nguyen', 'Tran', 'Patel', 'Garcia', 'Martinez', 'Rodriguez', 'Hernandez', 'Lopez', 'Ramirez',
         'Flores', 'Rivera', 'Reyes', 'Cruz', 'Chen', 'Park')),
    'en_uk': (
        ('Adam', 'Alastair', 'Benedict', 'Bradley', 'Cameron', 'Connor', 'Dominic', 'Ethan', 'Finley', 'Frederick',
         'Gabriel', 'Isaac', 'Jacob', 'Jasper', 'Leo', 'Liam', 'Louis', 'Mason', 'Miles', 'Noah', 'Oscar', 'Patrick',
         'Reuben', 'Sebastian', 'Theo', 'Tristan', 'Zachary', 'Harvey', 'Ralph'),
        ('Baxter', 'Bradshaw', 'Bramley', 'Burrows', 'Chapman', 'Coates', 'Dawson', 'Elliott', 'Gibson', 'Goddard',
         'Hardy', 'Hayward', 'Holmes', 'Hopkins', 'Kemp', 'Knight', 'Lambert', 'Lowe', 'Marshall', 'Mason',
         'Newton', 'Osborne', 'Payne', 'Ramsden', 'Read', 'Sharp', 'Slater', 'Spencer', 'Stone', 'Sutton', 'Tucker',
         'Webb', 'West', 'Whitehead', 'Wilkinson', 'Woodward', 'Ashton', 'Barker', 'Dyson', 'Gould', 'Harper',
         'Lister', 'Nicholson', 'Pearson', 'Royle', 'Stubbs', 'Townsend')),
    'aus': (
        ('Archie', 'Brayden', 'Callan', 'Declan', 'Dylan', 'Elijah', 'Flynn', 'Heath', 'Jarrah', 'Jesse', 'Kai',
         'Liam', 'Logan', 'Marcus', 'Max', 'Noah', 'Oscar', 'Patrick', 'Reuben', 'Rhys', 'Seb', 'Toby', 'Xavier',
         'Aaron', 'Caleb', 'Damien', 'Ethan', 'Harvey', 'Jordan', 'Kieran', 'Mason', 'Nathan', 'Owen', 'Taj'),
        ('Atherton', 'Barlow', 'Birch', 'Callaghan', 'Dawson', 'Doherty', 'Elliott', 'Fenton', 'Gallagher', 'Hammond',
         'Healy', 'Jamieson', 'Kerrigan', 'Lawler', 'Maddern', 'McGregor', 'Nicholls', "O'Brien", 'Pearce',
         'Quinlan', 'Rankin', 'Sheridan', 'Toohey', 'Upton', 'Walsh', 'Wheatley', 'Brennan', 'Cockburn', 'Donnelly',
         'Ellery', 'Fitzgerald', 'Gleeson', 'Hennessy', 'Kennedy', 'Macklin', 'Morrissey', 'Prendergast', 'Tully')),
    'jp': (
        ('Haruki', 'Itsuki', 'Asahi', 'Minato', 'Yamato', 'Sora', 'Hinata', 'Rintaro', 'Kotaro', 'Shinnosuke',
         'Ryota', 'Kenta', 'Yusuke', 'Kazuya', 'Tomohiro', 'Masato', 'Hideto', 'Takeshi', 'Tetsuya', 'Yuma', 'Koki',
         'Shunsuke', 'Yuya', 'Takuya', 'Naoya', 'Ryuji', 'Toshiki', 'Akihiro', 'Junpei', 'Kyohei', 'Soma', 'Eita',
         'Haruma', 'Rui', 'Tsubasa', 'Yuji', 'Makoto', 'Atsushi'),
        ('Nakano', 'Ono', 'Tamura', 'Takeuchi', 'Kaneko', 'Wada', 'Nakayama', 'Ishida', 'Ueda', 'Morita', 'Hara',
         'Shibata', 'Sakai', 'Kudo', 'Yokoyama', 'Miyazaki', 'Miyamoto', 'Uchida', 'Takagi', 'Ando', 'Taniguchi',
         'Ohno', 'Maruyama', 'Imai', 'Takada', 'Fujimoto', 'Murata', 'Ueno', 'Sugiyama', 'Masuda', 'Sugawara',
         'Hirano', 'Otsuka', 'Chiba', 'Kubo', 'Matsui', 'Iwasaki', 'Sakurai', 'Kinoshita', 'Noguchi', 'Matsuo',
         'Kikuchi', 'Nomura', 'Arai', 'Kawaguchi', 'Hirata', 'Oda', 'Kojima', 'Sano', 'Kubota', 'Shimada', 'Iwata',
         'Yano', 'Hattori', 'Higuchi', 'Tsuchiya', 'Kitamura', 'Kawakami', 'Nagai')),
    'kr': (
        ('Min-ho', 'Ji-hwan', 'Seong-jin', 'Hyun-soo', 'Jin-woo', 'Tae-yang', 'Joon-ho', 'Sang-woo', 'Kyu-min',
         'Yeon-woo', 'Ha-jun', 'Eun-woo', 'Si-woo', 'Yoon-ho', 'Jae-hyun', 'Seung-woo', 'Dong-wook', 'Min-seok',
         'Woo-hyun', 'Hyun-jin', 'Ki-hoon', 'Jong-min', 'Sung-hoon', 'Young-ho', 'Chan-woo', 'Jun-ho', 'Tae-min',
         'Ho-jin', 'Jin-seo', 'Seok-min', 'Kwang-hyun', 'Bum-soo', 'Ji-sung', 'Myung-ho', 'Won-jun', 'Jae-min',
         'Do-hyun', 'Gi-tae', 'Hae-sung', 'Jun-young', 'Kang-min', 'Sun-woo', 'Yong-jun', 'Hee-chan'),
        ('Bae', 'Noh', 'Ha', 'Kwak', 'Seong', 'Cha', 'Joo', 'Woo', 'Min', 'Na', 'Ryu', 'Jin', 'Chae', 'Won',
         'Byun', 'Do', 'Gil', 'Yeo', 'Kong', 'Hyun')),
    'th': (
        ('Arnon', 'Boonchu', 'Chaiwat', 'Chatchai', 'Ekachai', 'Jirapat', 'Kasem', 'Kriangsak', 'Manop', 'Narong',
         'Nopparat', 'Pairoj', 'Panya', 'Pongsak', 'Prasert', 'Sakda', 'Sombat', 'Sompong', 'Sutthipong', 'Teerapat',
         'Thanakorn', 'Thanawat', 'Wichai', 'Wisit', 'Yuthana', 'Apichart', 'Chakrit', 'Kritsada', 'Nattawut',
         'Rungroj', 'Supachai', 'Weerapong', 'Kanin', 'Pakorn', 'Siwakorn', 'Tanakrit'),
        ('Bunnag', 'Chaisiri', 'Chotiwat', 'Inthasorn', 'Jaroensuk', 'Kamolrat', 'Limsakul', 'Meechai', 'Nakprasert',
         'Ounsiri', 'Panyarat', 'Phothong', 'Ruangsri', 'Sangthong', 'Sirisombat', 'Somboon', 'Srisawat',
         'Suksawat', 'Thongdee', 'Udomsak', 'Wannasiri', 'Wongchai', 'Anantachai', 'Boonsong', 'Chuenchom',
         'Kaewmanee', 'Lertpanya', 'Maneerat', 'Pattanakul', 'Rattanaporn', 'Saelim', 'Thepsuwan')),
    'da': (
        ('Andreas', 'Bjørn', 'Casper', 'Daniel', 'Elias', 'Gustav', 'Henrik', 'Jakob', 'Jens', 'Kristian', 'Lucas',
         'Malthe', 'Martin', 'Morten', 'Niels', 'Noah', 'Oscar', 'Peter', 'Sebastian', 'Simon', 'Steffen', 'Tobias',
         'Troels', 'Ulrik', 'Valdemar', 'Viktor', 'William', 'Aksel', 'Alfred', 'Carl', 'Jeppe', 'Lars', 'Mikael',
         'Nikolaj', 'Philip', 'Claus', 'Johan'),
        ('Frandsen', 'Svendsen', 'Knudsen', 'Jakobsen', 'Mikkelsen', 'Lauridsen', 'Clausen', 'Simonsen', 'Laursen',
         'Kjeldsen', 'Frederiksen', 'Henriksen', 'Eriksen', 'Østergaard', 'Nørgaard', 'Christoffersen', 'Gregersen',
         'Brandt', 'Friis', 'Lindholm', 'Overgaard', 'Thygesen', 'Winther', 'Krogh', 'Iversen', 'Jeppesen',
         'Bertelsen', 'Danielsen', 'Holst', 'Kofoed', 'Riis', 'Storm', 'Toft', 'Villadsen')),
    'sv': (
        ('Albert', 'Anton', 'Arvid', 'Carl', 'Daniel', 'David', 'Edvin', 'Elliot', 'Felix', 'Gabriel', 'Gunnar',
         'Harald', 'Hjalmar', 'Ivar', 'Jacob', 'Joel', 'Kasper', 'Leo', 'Liam', 'Love', 'Magnus', 'Malte', 'Marcus',
         'Melker', 'Noah', 'Olle', 'Otto', 'Pontus', 'Rickard', 'Samuel', 'Simon', 'Sixten', 'Vincent', 'Wilhelm',
         'Folke', 'Göran'),
        ('Axelsson', 'Abrahamsson', 'Berg', 'Blomqvist', 'Dahlberg', 'Ek', 'Falk', 'Forsman', 'Hedlund',
         'Hermansson', 'Holm', 'Isaksson', 'Jakobsson', 'Lund', 'Lundberg', 'Lundgren', 'Lundqvist', 'Magnusson',
         'Mattsson', 'Nordin', 'Nordström', 'Nyberg', 'Ström', 'Söderberg', 'Sundberg', 'Sundström', 'Wikström',
         'Åberg', 'Öberg', 'Berggren', 'Dahlgren', 'Hellström', 'Lindström', 'Mårtensson', 'Norberg', 'Sandström',
         'Viklund', 'Westberg')),
    'zh': (
        ('Hongyu', 'Jiawei', 'Xiaolong', 'Zhiyuan', 'Yuxuan', 'Haoyu', 'Ziyang', 'Boyang', 'Chenxi', 'Guanyu',
         'Haotian', 'Jiaming', 'Jinpeng', 'Kaiwen', 'Mingxuan', 'Ruihao', 'Shengli', 'Tianhao', 'Weijie', 'Wenbo',
         'Xiangyu', 'Xinyu', 'Yanbin', 'Yicheng', 'Yuhang', 'Zehao', 'Zhenhua', 'Zixuan', 'Zhaoyang', 'Qiang',
         'Gang', 'Ning', 'Bin', 'Liang', 'Yong', 'Fan', 'Hang', 'Qi'),
        ('Peng', 'Zeng', 'Xiao', 'Tian', 'Dong', 'Pan', 'Yuan', 'Cai', 'Jiang', 'Yu', 'Du', 'Ye', 'Cheng', 'Wei',
         'Su', 'Ding', 'Ren', 'Shen', 'Yao', 'Lu', 'Cui', 'Zhong', 'Tan', 'Fan', 'Jin', 'Shi', 'Liao', 'Jia', 'Xia',
         'Fu', 'Fang', 'Bai', 'Zou', 'Meng', 'Xiong', 'Qin', 'Qiu', 'Hou', 'Yin', 'Xue', 'Yan', 'Duan', 'Lei', 'Kong',
         'Mao', 'Gu', 'Shao', 'Wan', 'Qian', 'Dai')),
    'no': (
        ('Adrian', 'Alexander', 'Anders', 'Bendik', 'Brage', 'Daniel', 'Elias', 'Emil', 'Erlend', 'Filip', 'Fredrik',
         'Gaute', 'Gunnar', 'Harald', 'Isak', 'Jonas', 'Jørgen', 'Kasper', 'Lars', 'Leon', 'Lucas', 'Mathias',
         'Marius', 'Noah', 'Oskar', 'Petter', 'Rasmus', 'Ruben', 'Sigurd', 'Simen', 'Snorre', 'Steinar', 'Sverre',
         'Theodor', 'Thomas', 'Trond', 'Vetle', 'Viktor', 'William', 'Øystein'),
        ('Bakke', 'Berge', 'Brekke', 'Dahle', 'Fjeld', 'Foss', 'Gundersen', 'Haugland', 'Hovland', 'Jacobsen',
         'Knutsen', 'Lund', 'Lunde', 'Myhre', 'Nygaard', 'Ødegaard', 'Rasmussen', 'Ruud', 'Sæther', 'Sandvik',
         'Skogen', 'Solheim', 'Svendsen', 'Tangen', 'Thorsen', 'Vik', 'Aas', 'Bjerke', 'Engen', 'Fossum', 'Hauge',
         'Iversen', 'Kvam', 'Lien', 'Mathisen', 'Nordby', 'Rønning', 'Strøm', 'Tveit')),
    'it': (
        ('Alberto', 'Antonio', 'Carlo', 'Cristian', 'Daniele', 'Dario', 'Enrico', 'Fabio', 'Giulio', 'Jacopo',
         'Manuel', 'Mattia', 'Nicola', 'Paolo', 'Roberto', 'Samuele', 'Simone', 'Valerio', 'Vittorio'),
        ('Amato', 'Barone', 'Bellini', 'Benedetti', 'Bernardi', 'Cattaneo', "D'Angelo", 'De Santis', 'Fabbri',
         'Farina', 'Ferri', 'Fiore', 'Grasso', 'Longo', 'Marchetti', 'Monti', 'Morelli', 'Palumbo', 'Parisi',
         'Pellegrini', 'Sala', 'Serra', 'Testa', 'Valentini', 'Villa', 'Vitale')),
    'in': (
        ('Abhinav', 'Akash', 'Amit', 'Anand', 'Ankit', 'Arnav', 'Ayaan', 'Deepak', 'Dhruv', 'Gaurav', 'Harsh',
         'Jai', 'Kunal', 'Mihir', 'Nikhil', 'Pranav', 'Raghav', 'Rajat', 'Sameer', 'Tanmay', 'Varun', 'Vivek',
         'Yash', 'Neel'),
        ('Agarwal', 'Bhat', 'Desai', 'Ghosh', 'Hegde', 'Jain', 'Kulkarni', 'Mishra', 'Pandey', 'Pandit', 'Rathore',
         'Sethi', 'Shetty', 'Sinha', 'Srinivasan', 'Tiwari', 'Trivedi', 'Venkatesh', 'Yadav', 'Kohli')),
}
BX = {b: (tuple(dict.fromkeys(given + EXTRA.get(b, ((), ()))[0])), tuple(dict.fromkeys(family + EXTRA.get(b, ((), ()))[1])))
      for b, (given, family) in B.items()}


def make_name(country, rng, taken, in_use=None):
    """A fictional name for a golfer from `country`. `taken`: every name used so far in the world.

    The starting world (`in_use` None) draws from the original banks and never repeats a name. Later
    arrivals (`in_use`: the names of people active now) draw from the larger banks: a name never used if
    one turns up, else one no active person holds (a retired person's name recurring, as names do across
    generations). A middle initial is the last resort (as some real tour players have)."""
    mix = NATION_BANKS[country]
    banks = B if in_use is None else BX

    def draw():
        bank = rng.choices([b for b, _ in mix], [w for _, w in mix])[0]
        given, family = banks[bank]
        return f'{rng.choice(given)} {rng.choice(family)}'

    def take(name):
        taken.add(name)
        if in_use is not None:
            in_use.add(name)
        return name
    for _ in range(500):
        name = draw()
        if name.lower() not in FAMOUS and name not in taken:
            return take(name)
    if in_use is not None:
        for _ in range(500):
            name = draw()
            if name.lower() not in FAMOUS and name not in in_use:
                return take(name)
    for _ in range(2000):
        bank = rng.choices([b for b, _ in mix], [w for _, w in mix])[0]
        given, family = banks[bank]
        name = f'{rng.choice(given)} {chr(65 + rng.randrange(26))}. {rng.choice(family)}'
        if name not in taken:
            return take(name)
    raise RuntimeError(f'could not name a golfer from {country}')
