def statuses():
    return [{'name': 'In backlog', 'color': 'blue'},
            {'name': 'In planning', 'color': 'orange'},
            {'name': 'In development', 'color': 'green'},
            {'name': 'Already exists', 'color': 'red'},
            {'name': 'Shipped', 'color': 'yellow'},
            {'name': 'In beta', 'color': 'purple'},
            {'name': 'Future', 'color': 'gray'},
            {'name': 'General', 'color': 'indigo'}]


def generate_comments():
    return ['This is a great idea! I love it!',
            'Yes please!',
            'I could really use this. Please implement this feature ASAP.',
            'I\'ve been waiting for this for a long time. Please make it happen.',
            'Same.',
            'Thanks for finally working on this!',
            'Any word on how long this will take to finish?',
            'Sounds like a great idea!',
            'Make it happen!',
            'Hi team, any update on this?',
            'This feature is an absolute MUST.',
            'Needed!',
            'Thanks!']


def generate_feedback():
    return [{'title': 'Allow users to add their own comment sections',
             'description':'It would be cool if users could have their own comment sections. I would love to be able to leave comments, and reply to other comments. Make it happen!'},
            {'title': 'Add a feedback feature to the website',
             'description':'Allow your users to collect feedback on this site. That would be awesome!'},
            {'title': 'User login and membership functionality',
             'description':'Allow users to sign up on your websites with a username & password. Enable/disable access to content/pages for different user types.'},
            {'title': 'Better Asset Management',
             'description':'Replace every instance of an asset throughout the project by replacing it in the Asset Manager'},
            {'title': 'Multi-language sites and CMS fields',
             'description':'Each page and CMS entry is translatable. When creating fields for a Collection, mark whether that field is translatable (some fields won\'t need translation, like references to other collections, price fields, etc). An option for Links should be added to choose a language (in addition to external links, pages within the site, etc).'},
            {'title': 'Sell Digital Goods',
             'description':'All we are looking for is selling a digital good, and creating unique links to be sent via email for now. A full "my account" experience would be nice down the road. '},
            {'title': 'Ability to style CSS Combinators: combo classes, pseudo classes, nested classes',
             'description':'When I add a css class and then add another css class on top of it, the resulting css rule in the code is a compound rule. Most of the time this is fine, but there are times I need the two rules to be separate. Please expand on the css layering, by giving us granular options for creating single-class or compound rules, and maybe even some complex bits like parent/sibling selectors, or ":" suffix rules.'
                'Mainly, if I\'ve got two elements, and one\'s got classes A->B->D while the other\'s got classes A->C->D, I don\'t want to have to define D twice, like I do now.'}]