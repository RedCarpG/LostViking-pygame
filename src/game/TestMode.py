class TestMode:
    """ Flags of the test mode (started from the main menu), never saved """

    enabled = False
    # The player can not be hit
    god_mode = False
    # Draw the outline of every sprite rect
    show_hitboxes = False

    @classmethod
    def reset(cls) -> None:
        cls.enabled = False
        cls.god_mode = False
        cls.show_hitboxes = False
