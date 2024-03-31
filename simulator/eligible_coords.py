class EligibleCoordinates:
    def __init__(self, coordinates):
        self.coordinates = coordinates

    def __contains__(self, item):
        return item in self.coordinates

    def __iter__(self):
        return iter(self.coordinates)

    def __len__(self):
        return len(self.coordinates)

    def __bool__(self):
        # An instance is considered True if it has any coordinates
        return bool(self.coordinates)


class LocationIndependent(EligibleCoordinates):
    def __init__(self):
        super().__init__(coordinates=[])  # No coordinates needed

    def __contains__(self, item):
        # Always true, indicating location independence
        return True

    def __iter__(self):
        # An empty iterator
        return iter(())

    def __bool__(self):
        # Always considered True, indicating the action is valid everywhere
        return True
