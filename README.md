# SemParsBoxer
A rudimentary Boxer-inspired semantic parser in Python. 


DRT is a semantic framework which aims at handling presupposition resolution within the context of a discourse: phenomena like anaphora are treated as such, and they can either be unified with existing referents (binding), or introduced as new referents (accomodation) in the discourse. DRT therefore offers a way of doing formal semantics in a format inspired by mental representations (SOURCE). 
For this purpose, boxes (DRS) are used, composed of a set of referents, and a set of conditions. Complex DRS conditions can be introduced, like negation or logical implication. Since the goal is to be able to offer a setting in which accomodation or binding can be done with respect to the restrictions of the discourse, the structure matters in order to be able to know which information can be accessed in which part of the discourse: this is done by checking for the acessibility condition. 
Constructing DRSs is a process that can be automated using the mapping to Lambda Calculus: Lambda-DRS, which is a subset of the global DRS language (source), and broadly expresses the body of a Lambda expression within a DRS. Provided that we have a clear mapping from syntax to semantics, we can then use lambda-calculus to construct parses for these sentences, ideally also applying binding and accomodation wrt to presuppositions as we go, in order to generate a full DRS given a discourse in natural language. 

This is what the Boxer semantic parser, written in Prolog, achieved. The parser first relies on the CCG syntactic framework, which assigns categories to tokens, that can then be combined in order to obtain a full sentence parse. The compositional nature of CCG makes it especially well-suited to combine with lambda calculus: ideally, we would map out each token-level category with a logic expression, and use the CCG rules to obtain the application order (or other transformations needed) and then constitute an equivalent semantic expression to be reduced. 
The original Boxer was written in Prolog. While Prolog is especially well-suited to handle Lambda-DRSs (with its built-in unification mechanism), the tools are currently not maintained. For this project, the goal was to see whether a Python-implementation of some of its aspects was doable. 

Other available tools: 
During this project, I took inspiration from ccg2lambda (which also contains a working version of the CandC parser): while CCG2lamnbda provides logical derivations from expressions built from CCGs the way I described above, it does not handle lambda-DRSs and relies on NLTK logic for the backend. 
While NLTK logic is infinitely more reliable in its lambda calculus application, I wanted to be able to have an intermediate representation for DRSs that would be quick to interpret given its equivalent in Prolog, for ease of implementation. Moreover, while the DRS module in NLTK logic is more advanced (it actually implements some parts of BAT like anaphora resolution), it requires the user to construct the DRS themselves, and does not provide an unified framework for the syntax to semantics mapping. I ran tests to make sure that the lambda calculus steps (free variable checking, alpha-conversion and beta-reduction) are actually equivalent in both modules (within the expressions available in the limited lexicon on my side of things). A future step would be to check the equivalence for more complex expressions, and possibly create a tool to convert from CCG-parsed Lambda DRS expressions to a representation NLTK Logic accepts. 


I composed the lexicon using the code available at: (in particular the folder). However, only a limited set of categories have been implemented so far. Moreover, the search for the logical expression corresponding to one parse leaf (defined as a python function, and based on CCG category and POS tag) in the Python dictionary mapping does not capture the unification logic of the mapping defined by Boxer (it is simply implemented as a nested Python dictionary). Finally, the CCG parser is not always accurate and can misinterpret homonyms (for instance, the 3rd person present verbs are often confused with plural nouns), and requires adjustements to obtain reliable parses (which is what the Boxer prolog does with numerous checks at the lexicon level). 

This parser implements complex DRS conditions like Negation, Logical Implication and Union, but does not attempt to implement Binding and Accommodation theory (anaphora resolution and so on are not dealt with here). 
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
- Variables constitute referents in the Predicate class, which contains a string symbol that represents their natural language meaning + any number of variables
- Relation is a class parallel to predicate, used to represent equality and membership (the described relation is passed as a string)
- Lambdas, containing the term and the body of the function
- Application, defines the variable/ function to be applied to another function. 
- DRS (made up of DRSRefs and DRSconditions) + complex DRSs (implemented are negation, logical implication and union)
- Merge: contains elements which can be joined (union is taken) into one DRS object

Files: 
- DRSclasses and LogicClasses respectively contain the objects needed to constitute a DRS expressions and to perform lambda calculus
- Lexicon: the lexicon is implemented as functions
- Mapping: Nested dictionnary mapping (using the CCG category as the first tier, and the POS as the second one) to the functions
- Substitution: contains the core lambda caculus logic, with a variable counter, a function to assign fresh variables while keeping track of the previous ones, the alpha reduction, substitution and beta-reduction operations
- showDRS: prints out the object DRS in the box format
- parse_sentences: calls the CandC tools to obtain parse a .txt file containing the sentences
- parse_CCG: recursively composes the Lambda calculus tree by traversing the XML parse, looking up the leaf nodes in the lexicon and then using the rules to infer the application order

How to run: 
1. Install ccg2lambda (for the CandC CCG parser)
2. From the CLI: create file with one sentence per row, and call run createDRS.py, passing the path to the file (default directory is assumed), as well as the output dir, and the path to the CandC tools from CCG2Lambda. 



