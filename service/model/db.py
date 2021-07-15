from peewee import *

import datetime
# CHOICES = [
#     (0,'REJECTED'),
#     (1,'DHCPDISCOVER'),
#     (3,'DHCPREQUEST')
# ]

db = SqliteDatabase('DHCPDATABASE.db')

class Mapping(Model):
    mac_address = CharField(unique=True)
    ip_address = CharField(unique=True)
    map_date = DateTimeField(default = datetime.datetime.now)
    lease_time = DateTimeField()
    
    
    class Meta:
        database = db

# class PermanentMap(Model):
#     xid = IntegerField(unique=True)
#     state = CharField(choices = CHOICES)
    
#     def get_state_label(self):
#         return dict(CHOICES)[self.state]

#     class Meta:
#         database = db
    

if __name__ == '__main__':
    db.connect()
    db.create_tables([Mapping])
    print('TABLES CREATED')
    db.close()