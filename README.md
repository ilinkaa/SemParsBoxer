# SemParsBoxer
A rudimentary Boxer-inspired DRS semantic parser in Python. 

This tool uses the CandC tools (and therefore relies on the CCG2lambda library) in order to obtain CCG-parses of natural language sentences. 
It implements complex DRS conditions like Negation, Logical Implication and Union, but does not try to implement Binding and Accomodation theory (anaphora resolution and so on are not dealt with here). 
Therefore, elements that are assigned Alfa-DRS are not currently implemented in the lexicon (e.g definite determiners, pronouns).

Currently working is beta-reduction on a limited set of constructions: 
- indefinite determiners
- transitive and intransitive verbs
- simple nouns / proper names
- simple prepositions
- VP negation (with auxiliary verbs), implemented with Negation DRS
- coordination (and / or, respectively implemented through Merge and Union)
- universal quantification (with the determiner "every")

The parser implements classes which mirror their Prolog predicate equivalents: 
- Variables are represented by the Var predicate, taking one string for their name as an argument.
- Variables constitute referents in the Predicate class, which contains a string symbol that represents their natural language meaning + any number of Variables
- Relation is a class parallel to predicate, used to represent equality and membership (the described relation is passed as a string)




