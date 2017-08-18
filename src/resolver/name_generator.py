
class NameGenerator:
    __index = 0

    def gen_name(self, prefix=None, ext=None) -> str:
        name = "file_" + str(NameGenerator.__index)
        NameGenerator.__index += 1

        if prefix:
            name = prefix+"_"+name

        if ext:
            name += ext

        if len(name) > 255:
            raise NameError

        return name
