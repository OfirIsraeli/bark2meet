from web_app.models import User

X_POS = 0
Y_POS = 1


class Areas:
    JERUSALEM = (31.771959, 35.217018)
    TEL_AVIV = (32.109333, 34.855499)
    MODIIN = (31.89670800658577, 35.007197003536874)
    BEER_SHEVA = (31.249006188313423, 34.78929831233399)

    Areas_dict = {
        (1.32, 2.43): set(),
        JERUSALEM: set(),
        TEL_AVIV: set(),
        MODIIN: set(),
        BEER_SHEVA: set()
    }

    def getUsersInRadius(self, user, radius):
        userLocationX = user.current_area_x
        userLocationY = user.current_area_y
        areaX = user.current_area_x
        areaY = user.current_area_y
        profilesInArea = self.Areas_dict[(areaX, areaY)]
        result = set()
        for profile in profilesInArea:
            dist = self.distance((areaX, areaY), userLocationX, userLocationY)
            if dist <= radius and profile.email is not user.email:
                result.add(profile)
        return result

    def init_areas(self):
        all_users = User.query.all()
        for user in all_users:
            self.update(user, True)

    def update(self, user, to_initialized=False):
        min_dist = 9999999
        curr_x_min = 9999999
        curr_y_min = 9999999
        #  delete user from old position in area dict
        if not to_initialized and \
                (user.current_area_x, user.current_area_y) in self.Areas_dict.keys():
            try:
                self.Areas_dict[(user.current_area_x, user.current_area_y)].remove(user)

            except:
                print("Error: Areas.update")

        for key in self.Areas_dict:
            curr_dist = self.distance(key, user.pos_x, user.pos_y)
            if curr_dist < min_dist:
                min_dist = curr_dist
                curr_x_min = key[X_POS]
                curr_y_min = key[Y_POS]

        # add user to relevant place in area dict only if he is not already in it
        not_add_user = False
        for user_in_area in self.Areas_dict[(curr_x_min, curr_y_min)]:
            if user_in_area.email == user.email:
                not_add_user = True
        if not not_add_user:
            self.Areas_dict[(curr_x_min, curr_y_min)].add(user)
        #print(self.Areas_dict)
        #print("\n\n\n\n")
        return curr_x_min, curr_y_min

    def distance(self, key, user_pos_x, user_pos_y):
        return (key[X_POS] - user_pos_x) ** 2 + (key[Y_POS] - user_pos_y) ** 2


area = Areas()
