import requests
import json
import memcache
from collections import defaultdict
import logging
from optparse import OptionParser
import sys

class FacebookUser:
    def __init__(self):
        self.friends = []
        self.distance_from_target = 100
        self.is_crawled = False
        self.data = defaultdict(str)
        self.is_cached = False

    def add_friend(self, other):
        ''' Add someone to this user's friends list. Not mutual. '''
        self.friends.append(other)
    
    def set_distance(self, distance):
        ''' Set distance (if closer) to the target person whose network
            we are trying to construct. '''
        if distance < self.distance_from_target:
            self.distance_from_target = distance
            self.is_cached = False

    def set_data(self, data):
        ''' Set profile info (from JSON objects). '''
        for key in data:
            self.data[key] = data[key]
        self.is_cached = False

    def distance(self):
        ''' Get distance to the target person whose network we are trying to
            construct. '''
        return self.distance_from_target

class FacebookGraph:

    def __init__(self, email, password, userid, mc=None):
        # Current user info
        self.email = email
        self.userid = userid
        self.password = password
        self.is_logged_in = False

        # Memcache object reference
        self.mc = mc

        # All users
        self.users = defaultdict(FacebookUser)

    def next_friend_to_crawl(self):
        ''' Returns next friend to crawl by choosing someone out of the list
            of friends we've discovered but haven't already crawled. '''
        possible_friends = filter(
            lambda id: self.users[id].distance() <= 2 and
                not self.users[id].is_crawled,
            self.users
        )
        if len(possible_friends) > 0:
            return possible_friends[0]

    def login(self):
        ''' Start a session on Facebook. Only call this when we need to make
            an actual request to the site. '''
        self.session = requests.session()

        logger.info('Logging in...')

        r = self.session.post(
            'http://m.facebook.com/login.php',
            data = {
                'email' : self.email,
                'pass'  : self.password
            }
        )
        self.is_logged_in = True

    def make_authorized_request(self, url, params=None):
        ''' Call this when we're making a request we have to be logged in for.
            Log in if we're not already. '''
        if not self.is_logged_in:
            self.login()

        return self.session.get(url, params=params)

    def fetch_friends_of(self, friendid):
        ''' Given a friendid, try to fetch their friends list from facebook.
            Decode JSON and simply return the .payload.entries contents.  '''

        # Try fetching from memcache
        if self.mc:
            friends_obj = self.mc.get('friends_' + str(friendid))
            if friends_obj is not None:
                return friends_obj

        logger.info('Requesting userid ' + str(friendid))
        r = self.make_authorized_request(
            'http://www.facebook.com/ajax/typeahead/profile_browser/' +
            'friends/bootstrap.php',
            {
                '__a'       : 1,
                'viewer'    : self.userid,
                'profile_id': friendid,
                '__user'    : self.userid
            }
        )

        friends_json = r.content.replace('for (;;);', '')
        friends_obj = json.loads(friends_json)['payload']['entries']
            
        if self.mc:
            logger.info('Storing userid ' + str(friendid))
            self.mc.set('friends_' + str(friendid), friends_obj)

        return friends_obj

    def add_friends_to_network(self, userid, friends_obj):
        ''' Go through a friend array (assuming they are all friends of userid)
            and add connections to our friend graph such that 'userid' and
            everyone in his friends list are connected. '''

        for friend in friends_obj:
            friendid = friend['uid']

            self.users[friendid].add_friend(userid)
            self.users[friendid].set_data(friend)

            self.users[userid].add_friend(friendid)

            # Find shortest distance for myself
            self.users[userid].set_distance(self.users[friendid].distance()+1)

        # Set shortest distance for friends
        for friend in friends_obj:
            friendid = friend['uid']
            self.users[friendid].set_distance(self.users[userid].distance()+1)

            logger.info('Added friends: %d - %d (%s, %d)', userid,
                friendid, friend['text'], self.users[friendid].distance())

        self.users[userid].is_crawled = True

    def print_dotfile(self, dotfile, display_distance):
        ''' Given a file handle and a distance of users to display within,
            print out the dotfile to the given file handle. '''

        # Find all users nearby-ish
        userids = filter(
            lambda id: self.users[id].distance() < display_distance,
            self.users
        )

        dotfile.write('graph g {\nratio=0.5;\n')

        # Print users out to dotfile
        for userid in userids:

            logger.info("User " + self.users[userid].data['text'] +
                " has distance " + str(self.users[userid].distance()))

            # Remove special characters, graphviz doesn't like
            name = "".join(
                filter(
                    lambda x: ord(x)<128,
                    self.users[userid].data['text']
                )
            )
            dotfile.write('\t{0} [label="{1}"];\n'.format(userid, name))

            for friendid in self.users[userid].friends:
                # Remove special characters, graphviz doesn't like
                name = "".join(
                    filter(
                        lambda x: ord(x)<128,
                        self.users[friendid].data['text']
                    )
                )
                dotfile.write('\t{0} [label="{1}"];\n'.format(friendid, name))

                # Only print each connection once, this isn't twitter
                if (friendid < userid or
                    self.users[friendid].distance() == display_distance):
                    dotfile.write('\t{0} -- {1};\n'.format(userid, friendid))

        dotfile.write('}\n')


def main():
    parser = OptionParser()
    parser.add_option("-e", "--email", dest="email",
        help="email of user to log in as (required)")
    parser.add_option("-p", "--password", dest="password",
        help="password of user to log in as (required)")
    parser.add_option("-u", "--userid", dest="userid",
        help="userid of user to log in as (required)")
    parser.add_option("-t", "--target", dest="target",
        help="target user (might be hidden) to construct network around (required)")
    parser.add_option("-s", "--start", dest="startat",
        help="userid of target's friend to start crawling at (required)")
    parser.add_option("-m", "--memcache", dest="memcache",
        help="memcache host/port, if available")
    parser.add_option("-i", "--info", dest="debug",
        action="store_true", default=False, help="print INFO-level logs")
    parser.add_option("-o", "--output", dest="filename",
        help="file to store DOT-file in, otherwise printed to stdout.")
    parser.add_option("-d", "--distance", dest="distance",
        default=3, help="distance to print")

    (options, args) = parser.parse_args()

    # Memcache, if specified.
    mc = memcache.Client([options.memcache]) if options.memcache else None

    # Logging
    if options.debug:
        logger.setLevel(logging.INFO)

    # Check required options
    if not (options.email and
            options.password and 
            options.userid and 
            options.startat and 
            options.target):
        sys.stderr.write("email, password, userid, startat, target are all " +
            "required parameters. See --help for more info.")
        sys.exit()

    # Login as this user
    fg = FacebookGraph(options.email, options.password, options.userid, mc)

    # Target user (Jesse)
    target_id = options.target
    fg.users[target_id].set_distance(0)
    # User to start crawling from
    fg.users[options.startat].set_distance(1)

    # Fetch users from memcache first, if possible
    if mc:
        userids_list = mc.get('userids')
        if userids_list is not None:
            for userid in userids_list:
                user_obj = mc.get('user_' + str(userid))
                if user_obj is not None:
                    fg.users[userid] = user_obj
                    fg.users[userid].is_cached = True
                    logger.info('Fetched user ' + str(userid) + ' from memcache')

    # Perform BFS on friends list, discovering the graph as we go
    while True:
        next_friend = fg.next_friend_to_crawl()
        if next_friend is None:
            break

        friends_list_two = fg.fetch_friends_of(next_friend)
        fg.add_friends_to_network(next_friend, friends_list_two)

    # Stuff results into memcache, if possible
    if mc:
        mc.set('userids', fg.users.keys())
        for userid in fg.users:
            if not fg.users[userid].is_cached:
                mc.set('user_' + str(userid), fg.users[userid])
                logger.info('Stored user ' + str(userid) + ' in memcache')

    # Default to stdout unless filename was provided
    output = open(options.filename, 'w+') if options.filename else sys.stdout

    fg.print_dotfile(output, options.distance)

    logger.info("Counted " + str(len(fg.users)) + " people")


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)-15s %(message)s')
    logger = logging.getLogger('crawler')
    main()

