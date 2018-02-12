import graphene
import requests
import json

def make_dict(result_list):
    result = {}
    for item in result_list:
        predicate = str(item[0])
        value = str(item[1])
        item_exists = result.get(predicate)
        if item_exists:
            result[predicate].append(value)
        else:
            result[predicate] = [value, ]
    return result

class TripleStoreInfo(graphene.ObjectType):
    size = graphene.Int()
    types = graphene.List(graphene.String)
    vocab = graphene.List(graphene.String)

    def resolve_size(self, args, context, info):
        headers = {'Content-Type': 'application/text'}
        query = '''
            select (count(*) as ?total) {
                ?s ?p ?o .
            }
        '''
        response = requests.post('http://localhost:5000/sparql', headers=headers, data=query)
        result = int(json.loads(response.text)['data'][0][0])
        return result

    def resolve_types(self, args, context, info):
        headers = {'Content-Type': 'application/text'}
        query = '''
            select distinct ?o {
                ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o .
            }
        '''
        response = requests.post('http://localhost:5000/sparql', headers=headers, data=query)
        list_of_lists = json.loads(response.text)['data']
        flattened_list = [item for items in list_of_lists for item in items]
        return flattened_list

    def resolve_vocab(self, args, context, info):
        headers = {'Content-Type': 'application/text'}
        query = '''
            select distinct ?p {
                ?s ?p ?o .
            }
        '''
        response = requests.post('http://localhost:5000/sparql', headers=headers, data=query)
        list_of_lists = json.loads(response.text)['data']
        flattened_list = [item for items in list_of_lists for item in items]
        return flattened_list


class IPerson(graphene.Interface):
    subject = graphene.String()
    name = graphene.String()
    description = graphene.String()
    birth_date = graphene.String()

class Person(graphene.ObjectType):
    class Meta:
        interfaces = (IPerson, )

    def resolve_type(self, args, context, info):
        headers = {'Content-Type': 'application/text'}
        query = '''
             select ?p ?o{
                 <%s> ?p ?o .
             }
         ''' % args['subject']
        response = requests.post('http://localhost:5000/sparql', headers=headers, data=query)
        list_of_lists = json.loads(response.text)['data']
        person_as_dict = make_dict((list_of_lists))
        name = person_as_dict.get("http://xmlns.com/foaf/0.1/name")[0] if person_as_dict.get("http://xmlns.com/foaf/0.1/name") else "unknown"
        description = person_as_dict.get("http://purl.org/dc/terms/description")[0] if person_as_dict.get("http://purl.org/dc/terms/description") else "unknown"
        birth_date = person_as_dict.get("http://dbpedia.org/ontology/birthDate")[0] if person_as_dict.get("http://dbpedia.org/ontology/birthDate") else "unknown"
        return Person(subject=args['subject'],
                      name=name,
                      description=description,
                      birth_date=birth_date)


class People(graphene.ObjectType):
    class Meta:
        interfaces = (IPerson, )
    count = graphene.Int()
    peopleList = graphene.List(Person)

    def resolve_count(self, args, context, info):
        headers = {'Content-Type': 'application/text'}
        query = '''
            select (count(*) as ?n) {
                ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Person> .
            }
        '''
        response = requests.post('http://localhost:5000/sparql', headers=headers, data=query)
        result = int(json.loads(response.text)['data'][0][0])
        return result

    def resolve_peopleList(self, args, context, info):
        headers = {'Content-Type': 'application/text'}
        query = '''
            select ?s {
                ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Person> .
            }
        '''
        response = requests.post('http://localhost:5000/sparql', headers=headers, data=query)
        list_of_lists = json.loads(response.text)['data']
        people = []
        for items in list_of_lists:
            for item in items:
                args['subject'] = item
                person = Person.resolve_type(Person, args, context, info)
                people.append(person)  # = [Person(subject=item) for items in list_of_lists for item in items]
        return people


class Query(graphene.ObjectType):
    info = graphene.Field(TripleStoreInfo)
    people = graphene.Field(People)
    person = graphene.Field(Person, subject=graphene.String())

    def resolve_info(self, args, context, info):
        return TripleStoreInfo()

    def resolve_people(self, args, context, info):
        return People()

    def resolve_person(self, args, context, info):
        return Person.resolve_type(Person, args, context, info)

schema = graphene.Schema(query=Query)

res = schema.execute('''
  query {
    info {
        size
        vocab
    }
    people {
        count    
        peopleList {
            subject
            name
            description
            birthDate
        }
    }
    person (subject:"http://dbpedia.org/resource/William_Shakespeare") {
        name
        description
        subject
    }    
  }
''')

if res.data:
    output = res.data
else:
    output = res.errors
for item in output['people']['peopleList']:
    print(item)
print(output['info']['size'])
print(output['info']['vocab'])
