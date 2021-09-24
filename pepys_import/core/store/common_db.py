from pprint import pprint

from prompt_toolkit import prompt
from prompt_toolkit.validation import Validator
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import backref, declared_attr, relationship
from tqdm import tqdm

from config import LOCAL_BASIC_TESTS, LOCAL_ENHANCED_TESTS
from pepys_import.core.formats import unit_registry
from pepys_import.core.formats.location import Location
from pepys_import.core.store import constants
from pepys_import.core.validators import constants as validation_constants
from pepys_import.core.validators.basic_validator import BasicValidator
from pepys_import.core.validators.enhanced_validator import EnhancedValidator
from pepys_import.utils.data_store_utils import chunked_list, shorten_uuid
from pepys_import.utils.import_utils import import_validators
from pepys_import.utils.sqlalchemy_utils import get_primary_key_for_table
from pepys_import.utils.text_formatting_utils import format_error_menu

LOCAL_BASIC_VALIDATORS = import_validators(LOCAL_BASIC_TESTS)
LOCAL_ENHANCED_VALIDATORS = import_validators(LOCAL_ENHANCED_TESTS)


class HostedByMixin:
    _default_preview_fields = ["subject_name", "host_name", "hosted_from", "hosted_to"]
    _default_dropdown_fields = ["subject_name", "host_name"]

    @declared_attr
    def subject(self):
        return relationship(
            "Platform",
            lazy="joined",
            join_depth=1,
            uselist=False,
            foreign_keys="HostedBy.subject_id",
        )

    @declared_attr
    def subject_name(self):
        return association_proxy("subject", "name")

    @declared_attr
    def host(self):
        return relationship(
            "Platform", lazy="joined", uselist=False, foreign_keys="HostedBy.host_id"
        )

    @declared_attr
    def host_name(self):
        return association_proxy("host", "name")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")


class SensorMixin:
    _default_preview_fields = ["name", "host__name", "sensor_type_name"]
    _default_dropdown_fields = ["name", "host__name", "host__identifier", "host__nationality_name"]

    @declared_attr
    def sensor_type(self):
        return relationship("SensorType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def sensor_type_name(self):
        return association_proxy("sensor_type", "name")

    @declared_attr
    def host_(self):
        return relationship("Platform", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def host__name(self):
        return association_proxy("host_", "name")

    @declared_attr
    def host__identifier(self):
        return association_proxy("host_", "identifier")

    @declared_attr
    def host__nationality_name(self):
        return association_proxy("host_", "nationality_name")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    def __repr__(self):
        return (
            f"Sensor(id={shorten_uuid(self.sensor_id)}, name={self.name}, "
            f"host={shorten_uuid(self.host)}, host__name={self.host__name}, "
            f"sensor_type={shorten_uuid(self.sensor_type_id)}, "
            f"sensor_type__name={self.sensor_type_name})"
        )

    @classmethod
    def find_sensor(cls, data_store, sensor_name, platform_id):
        """
        This method tries to find a Sensor entity with the given sensor_name. If it
        finds, it returns the entity. If it is not found, it searches synonyms.

        :param data_store: A :class:`DataStore` object
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: String
        :param platform_id:  Primary key of the Platform that Sensor belongs to
        :type platform_id: int
        :return:
        """
        # If we don't have a sensor name then we can't search by name!
        if sensor_name is None:
            return None

        cached_result = data_store._sensor_cache.get((sensor_name, platform_id))
        if cached_result:
            return cached_result

        sensor = (
            data_store.session.query(data_store.db_classes.Sensor)
            .filter(data_store.db_classes.Sensor.name == sensor_name)
            .filter(data_store.db_classes.Sensor.host == platform_id)
            .first()
        )
        if sensor:
            data_store.session.expunge(sensor)
            data_store._sensor_cache[(sensor_name, platform_id)] = sensor
            return sensor

        return None


class PlatformMixin:
    _default_preview_fields = ["name", "identifier", "nationality_name", "platform_type_name"]
    _default_dropdown_fields = ["name", "identifier", "nationality_name"]

    @declared_attr
    def wargame_participations(self):
        return association_proxy("participations", "wargame_name")

    @declared_attr
    def platform_type(self):
        return relationship("PlatformType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def platform_type_name(self):
        return association_proxy("platform_type", "name")

    @declared_attr
    def nationality(self):
        return relationship("Nationality", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def nationality_name(self):
        return association_proxy("nationality", "name")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    def __repr__(self):
        return f'Platform(name="{self.name}", identifier="{self.identifier}", nationality="{self.nationality_name}"'

    def get_sensor(
        self,
        data_store,
        sensor_name=None,
        sensor_type=None,
        privacy=None,
        change_id=None,
    ):
        """
         Lookup or create a sensor of this name for this :class:`Platform`.
         Specified sensor will be added to the :class:`Sensor` table.
         It uses find_sensor method to search existing sensors.

        :param data_store: DataStore object to to query DB and use missing data resolver
        :type data_store: DataStore
        :param sensor_name: Name of :class:`Sensor`
        :type sensor_name: String
        :param sensor_type: Type of :class:`Sensor`
        :type sensor_type: String
        :param privacy: Privacy of :class:`Sensor`
        :type privacy: String
        :param change_id: ID of the :class:`Change` object
        :type change_id: Integer or UUID
        :return: Created :class:`Sensor` entity
        :rtype: Sensor
        """
        Sensor = data_store.db_classes.Sensor

        sensor = Sensor().find_sensor(data_store, sensor_name, self.platform_id)
        if sensor:
            return sensor

        sensor_type_obj = data_store.search_sensor_type(sensor_type)
        privacy_obj = data_store.search_privacy(privacy)
        if sensor_type_obj is None or privacy_obj is None:
            resolved_data = data_store.missing_data_resolver.resolve_sensor(
                data_store, sensor_name, sensor_type, self.platform_id, privacy, change_id
            )
            # It means that new sensor added as a synonym and existing sensor returned
            if isinstance(resolved_data, Sensor):
                return resolved_data
            elif len(resolved_data) == 3:
                (
                    sensor_name,
                    sensor_type_obj,
                    privacy_obj,
                ) = resolved_data

        assert isinstance(
            sensor_type_obj, data_store.db_classes.SensorType
        ), "Type error for Sensor Type entity"
        assert isinstance(
            privacy_obj, data_store.db_classes.Privacy
        ), "Type error for Privacy entity"

        return data_store.add_to_sensors(
            name=sensor_name,
            sensor_type=sensor_type_obj.name,
            host_name=None,
            host_nationality=None,
            host_identifier=None,
            host_id=self.platform_id,
            privacy=privacy_obj.name,
            change_id=change_id,
        )


class SeriesMixin:
    _default_preview_fields = ["name"]
    _default_dropdown_fields = ["name"]

    @declared_attr
    def child_wargames(self):
        return relationship(
            "Wargame",
            lazy="joined",
            backref=backref("series", lazy="joined"),
            order_by="asc(Wargame.created_date)",
        )

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    # TODO: May or may not be needed, depending how we handle these objects
    # in the GUI
    # def create_exercise(self, data_store, name, start, end, privacy):
    #     privacy = data_store.search_privacy(privacy)
    #     if privacy is None:
    #         raise ValueError("Specified Privacy does not exist")

    #     exercise = data_store.db_classes.Exercise(name=name, start=start, end=end)
    #     exercise.privacy = privacy
    #     exercise.series = self

    #     data_store.session.add(exercise)
    #     data_store.session.flush()

    def __repr__(self):
        return f'Series(name="{self.name}")'


class WargameMixin:
    _default_preview_fields = ["name", "start", "end"]
    _default_dropdown_fields = ["name"]

    @declared_attr
    def child_serials(self):
        return relationship(
            "Serial",
            lazy="joined",
            backref=backref("wargame", lazy="joined"),
            passive_deletes=True,
            cascade="all, delete, delete-orphan",
            order_by="asc(Serial.start)",
        )

    @declared_attr
    def participants(self):
        return relationship(
            "WargameParticipant",
            passive_deletes=True,
            cascade="all, delete, delete-orphan",
            lazy="joined",
            order_by="asc(WargameParticipant.created_date)",
            back_populates="wargame",
            uselist=True,
            info={"skip_in_gui": True},
        )

    @declared_attr
    def participants_platform_name(self):
        return association_proxy("participants", "platform_name")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def series_name(self):
        return association_proxy("series", "name")

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    def add_participant(self, data_store, platform, privacy, change_id):
        """Add a new participant to this Wargame. This creates a WargameParticipant entry.

        :param data_store: DataStore
        :type data_store: DataStore
        :param platform: Platform to add as a participant
        :type platform: Platform object or Platform ID value
        :param privacy: Privacy to assign to this participant
        :type privacy: str
        :param change_id: Change ID for this change
        :type change_id: Change ID
        :return: Newly created WargameParticipant object
        :rtype: WargameParticipant
        """
        privacy = data_store.search_privacy(privacy)
        if privacy is None:
            raise ValueError("Specified Privacy does not exist")

        if not isinstance(platform, data_store.db_classes.Platform):
            platform = (
                data_store.session.query(data_store.db_classes.Platform)
                .filter(data_store.db_classes.Platform.platform_id == platform)
                .one()
            )

        data_store.session.expunge_all()

        participant = data_store.db_classes.WargameParticipant()
        participant.wargame = self
        participant.privacy_id = privacy.privacy_id
        participant.platform_id = platform.platform_id

        data_store.session.add(participant)
        data_store.session.flush()
        data_store.session.refresh(self)

        data_store.add_to_logs(
            table=constants.WARGAME_PARTICIPANT,
            row_id=participant.wargame_participant_id,
            change_id=change_id,
        )

        data_store.session.expunge_all()

        return participant

    # This can be a useful shorthand, but adding a platform by appending to the list that
    # this provides doesn't work, so this is actually a dangerous attribute to have around!
    # @declared_attr
    # def participant_platforms(self):
    #     return association_proxy("participants", "platform")

    def __repr__(self):
        return f'Wargame(name="{self.name}")'


class SerialMixin:
    _default_preview_fields = ["serial_number", "start", "end"]
    _default_dropdown_fields = ["serial_number"]

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def wargame_name(self):
        return association_proxy("wargame", "name")

    @declared_attr
    def participants_platform_name(self):
        return association_proxy("participants", "platform_name")

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    def add_participant(
        self,
        data_store,
        wargame_participant,
        force_type,
        privacy,
        start=None,
        end=None,
        change_id=None,
    ):
        """Add a participant to this Serial. This creates a SerialParticipant object.

        :param data_store: DataStore
        :type data_store: DataStore
        :param wargame_participant: Wargame participant which defines the Platform that this SerialParticipant is representing
        :type wargame_participant: WargameParticipant or WargameParticipant ID value
        :param force_type: Force to assign this participant
        :type force_type: str ("Blue" or "Red" normally)
        :param privacy: Privacy to assign this participant
        :type privacy: str
        :param start: Start timestamp for this participant, defaults to None
        :type start: datetime, optional
        :param end: End timestamp for this participant, defaults to None
        :type end: datetime, optional
        :param change_id: Change ID for this change, defaults to None
        :type change_id: ID, optional
        :return: New SerialParticipant instance
        :rtype: SerialParticipant
        """
        privacy = data_store.search_privacy(privacy)
        if privacy is None:
            raise ValueError("Specified Privacy does not exist")

        if force_type == "Red":
            color = "#ff0000"
        elif force_type == "Blue":
            color = "#0000ff"

        # This searches for the force type first, and if it exists then it returns
        # it. Otherwise it creates it.
        force_type = data_store.add_to_force_types(force_type, color, change_id)

        if not isinstance(wargame_participant, data_store.db_classes.WargameParticipant):
            wargame_participant = (
                data_store.session.query(data_store.db_classes.WargameParticipant)
                .filter(
                    data_store.db_classes.WargameParticipant.wargame_participant_id
                    == wargame_participant
                )
                .one()
            )

        data_store.session.expunge_all()

        participant = data_store.db_classes.SerialParticipant()
        participant.serial = self
        participant.privacy_id = privacy.privacy_id
        participant.wargame_participant_id = wargame_participant.wargame_participant_id
        participant.start = start
        participant.end = end
        participant.force_type_id = force_type.force_type_id

        data_store.session.add(participant)
        data_store.session.flush()
        data_store.session.refresh(participant.serial)

        data_store.add_to_logs(
            table=constants.SERIAL_PARTICIPANT,
            row_id=participant.serial_participant_id,
            change_id=change_id,
        )

        data_store.session.expunge_all()

        return participant

    def __repr__(self):
        return f'Serial(serial_number="{self.serial_number}")'


class WargameParticipantMixin:
    _default_preview_fields = ["platform_name", "wargame_name"]
    _default_dropdown_fields = ["platform_name", "wargame_name"]

    @declared_attr
    def wargame(self):
        return relationship("Wargame", lazy="joined", back_populates="participants")

    @declared_attr
    def platform(self):
        return relationship(
            "Platform",
            lazy="joined",
            backref=backref("participations", info={"skip_in_gui": True}),
        )

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")

    @declared_attr
    def platform_identifier(self):
        return association_proxy("platform", "identifier")

    @declared_attr
    def platform_nationality_name(self):
        return association_proxy("platform", "nationality_name")

    @declared_attr
    def wargame_name(self):
        return association_proxy("wargame", "name")

    def __repr__(self):
        return f'WargameParticipant(wargame="{self.wargame_name}", platform="{self.platform_name}")'


class SerialParticipantMixin:
    _default_preview_fields = ["serial_number", "platform_name"]
    _default_dropdown_fields = ["serial_number", "platform_name"]

    @declared_attr
    def serial(self):
        return relationship(
            "Serial",
            lazy="joined",
            backref=backref(
                "participants",
                passive_deletes=True,
                cascade="all, delete, delete-orphan",
                lazy="joined",
                info={"skip_in_gui": True},
            ),
        )

    @declared_attr
    def wargame_participant(self):
        return relationship(
            "WargameParticipant",
            lazy="joined",
            backref=backref(
                "serial_participants",
                lazy="joined",
                passive_deletes=True,
                cascade="all, delete, delete-orphan",
                info={"skip_in_gui": True},
            ),
        )

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    @declared_attr
    def force_type(self):
        return relationship("ForceType", lazy="joined")

    @declared_attr
    def force_type_name(self):
        return association_proxy("force_type", "name")

    @declared_attr
    def force_type_color(self):
        return association_proxy("force_type", "color")

    @declared_attr
    def serial_number(self):
        return association_proxy("serial", "serial_number")

    @declared_attr
    def serial_exercise(self):
        return association_proxy("serial", "serial_exercise")

    @declared_attr
    def platform(self):
        return association_proxy("wargame_participant", "platform")

    @declared_attr
    def platform_name(self):
        return association_proxy("wargame_participant", "platform_name")

    @declared_attr
    def platform_identifier(self):
        return association_proxy("wargame_participant", "platform_identifier")

    @declared_attr
    def platform_nationality_name(self):
        return association_proxy("wargame_participant", "platform_nationality_name")

    def __repr__(self):
        return f'SerialParticipant(serial="{self.serial_number}, platform="{self.platform_name})"'


class DatafileMixin:
    _default_preview_fields = ["reference", "datafile_type_name"]
    _default_dropdown_fields = ["reference"]

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    @declared_attr
    def datafile_type(self):
        return relationship("DatafileType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def datafile_type_name(self):
        return association_proxy("datafile_type", "name")

    def flush_extracted_tokens(self):
        """Flush the current list of extracted tokens out to the dict linking measurement
        objects to tokens, ready for writing to the database at the end of the import.

        This should be called when all the extractions have been done for a _single_ measurement
        object (State/Contact etc). Often this will be at the end of the `_load_this_line()` method,
        but in more complex importers it may be needed elsewhere."""
        if len(self.pending_extracted_tokens) == 0:
            return

        # If there aren't any tokens recorded for this measurement object already
        # then put the list into the dict. If there are already tokens recorded, then append the list
        # to the list that's already in the dict
        if (
            self.measurement_object_to_tokens_list.get(self.current_measurement_object, None)
            is None
        ):
            self.measurement_object_to_tokens_list[
                self.current_measurement_object
            ] = self.pending_extracted_tokens
        else:
            self.measurement_object_to_tokens_list[
                self.current_measurement_object
            ] += self.pending_extracted_tokens

        self.pending_extracted_tokens = []

    def create_state(self, data_store, platform, sensor, timestamp, parser_name):
        """Creates a new State object to record information on the state of a particular
        platform at a specific time.

        :param data_store: DataStore connected to the database that the State object should be
        created in
        :type data_store: DataStore
        :param platform: Platform that the State is recording information about
        :type platform: Platform
        :param sensor: Sensor used to record this state information
        :type sensor: Sensor
        :param timestamp: Timestamp of the State information
        :type timestamp: datetime.datetime
        :param parser_name: Name of parser used to import the data for this State
        :type parser_name: String
        :return: Newly-created State object
        :rtype: State

        Note: The State object will automatically be added to a list of pending
        State objects (stored in Datafile.measurements) which will be committed to the database
        later, if the full import succeeds.
        """
        state = data_store.db_classes.State(
            sensor_id=sensor.sensor_id,
            time=timestamp,
            source_id=self.datafile_id,
            sensor=sensor,
            platform=platform,
        )
        self.add_measurement_to_dict(state, parser_name)

        self.current_measurement_object = state
        return state

    def create_contact(self, data_store, platform, sensor, timestamp, parser_name):
        """Creates a new Contact object to record information on a Contact observed by a particular
        platform at a specific time.

        :param data_store: DataStore connected to the database that the Contact object should be
        created in
        :type data_store: DataStore
        :param platform: Platform that the Contact was observed from
        :type platform: Platform
        :param sensor: Sensor used to record this Contact information
        :type sensor: Sensor
        :param timestamp: Timestamp of the Contact information
        :type timestamp: datetime.datetime
        :param parser_name: Name of parser used to import the data for this Contact
        :type parser_name: String
        :return: Newly-created Contact object
        :rtype: Contact

        Note: The Contact object will automatically be added to a list of pending
        Contact objects (stored in Datafile.measurements) which will be committed to the database
        later, if the full import succeeds.
        """
        contact = data_store.db_classes.Contact(
            sensor_id=sensor.sensor_id,
            time=timestamp,
            source_id=self.datafile_id,
            sensor=sensor,
            platform=platform,
        )
        self.add_measurement_to_dict(contact, parser_name)
        self.current_measurement_object = contact
        return contact

    def create_comment(
        self,
        data_store,
        platform,
        timestamp,
        comment,
        comment_type,
        parser_name,
    ):
        """Creates a new Comment object to record textual information logged by a particular
        platform at a specific time.

        :param data_store: DataStore connected to the database that the Comment object should be
        created in
        :type data_store: DataStore
        :param platform: Platform that the Comment was recorded from
        :type platform: Platform
        :param timestamp: Timestamp of the Comment information
        :type timestamp: datetime.datetime
        :param comment: Text of the comment
        :type comment: String
        :param comment_type: Type of the comment
        :type comment_type: CommentType
        :return: Newly-created Comment object
        :rtype: Comment

        Note: The Comment object will automatically be added to a list of pending
        Comment objects (stored in Datafile.measurements) which will be committed to the database
        later, if the full import succeeds.
        """
        comment = data_store.db_classes.Comment(
            platform_id=platform.platform_id,
            time=timestamp,
            content=comment,
            comment_type_id=comment_type.comment_type_id,
            source_id=self.datafile_id,
            platform=platform,
        )
        self.add_measurement_to_dict(comment, parser_name)
        self.current_measurement_object = comment
        return comment

    def create_geometry(self, data_store, geom, geom_type_id, geom_sub_type_id, parser_name):
        geometry = data_store.db_classes.Geometry1(
            geometry=geom,
            source_id=self.datafile_id,
            geo_type_id=geom_type_id,
            geo_sub_type_id=geom_sub_type_id,
        )
        self.add_measurement_to_dict(geometry, parser_name)
        self.current_measurement_object = geometry
        return geometry

    def create_activation(self, data_store, sensor, start, end, parser_name):
        activation = data_store.db_classes.Activation(
            sensor_id=sensor.sensor_id,
            start=start,
            end=end,
            source_id=self.datafile_id,
        )
        self.add_measurement_to_dict(activation, parser_name)
        self.current_measurement_object = activation
        return activation

    def add_measurement_to_dict(self, measurement, parser_name):
        try:
            platform_id = measurement.platform_id
        except AttributeError:
            # Platform ID doesn't exist for Geometry1 objects, so
            # use a platform of 'N/A'
            platform_id = "N/A"

        # Cache objects according to their platform
        if platform_id not in self.measurements[parser_name]:
            self.measurements[parser_name][platform_id] = list()

        self.measurements[parser_name][platform_id].append(measurement)

    def _input_validator(self):
        def is_valid(option):
            return option == str(1) or option == str(2)

        validator = Validator.from_callable(
            is_valid,
            error_message="You didn't select a valid option",
            move_cursor_to_end=True,
        )
        return validator

    def _ask_user_what_they_want(self, error, ask_skipping_validator, skip_validator):
        validator = self._input_validator()
        title = f"\n\nError! Message: {error}.\nWould you like to\n"
        choices = (
            "Skip enhanced validator for this file",
            "Carry on running the validator, logging errors",
        )
        choices_text = ""
        for index, choice in enumerate(choices, 1):
            choices_text += f"   {str(index)}) {choice}\n"
        choice = prompt(format_error_menu(title, choices_text), validator=validator)
        delete = False
        if choice == "1":
            ask_skipping_validator = False
            skip_validator = True
            delete = True
        elif choice == "2":
            ask_skipping_validator = False
        return ask_skipping_validator, skip_validator, delete

    def validate(
        self,
        validation_level=validation_constants.NONE_LEVEL,
        errors=None,
        parser="Default",
        skip_validation=False,
    ):
        # If there is no parsing error, it will return None. If that's the case,
        # create a new list for validation errors.
        if errors is None:
            errors = list()
        assert isinstance(errors, list), "Type error for errors!"

        failed_validators = []

        # If skip_validation is True or validation_level is None,
        # return True without running any validator
        if skip_validation or validation_level == validation_constants.NONE_LEVEL:
            return (True, failed_validators)
        elif validation_level == validation_constants.BASIC_LEVEL:
            # Create validator objects here so we're only creating them once
            bv = BasicValidator(parser)
            local_bv_objects = [bv(parser) for bv in LOCAL_BASIC_VALIDATORS]
            print(f"Running basic validation for {parser}")
            for measurement in tqdm(self.measurements[parser]):
                # Run the standard Basic Validator
                if not bv.validate(measurement, errors):
                    failed_validators.append(bv.name)
                # Run all the basic validators in the folder configured in the config file
                for local_bv in local_bv_objects:
                    if not local_bv.validate(measurement, errors):
                        failed_validators.append(bv.name)
            print("Basic validator errors")
            pprint(errors)
            if not errors:
                return (True, failed_validators)
            return (False, failed_validators)
        elif validation_level == validation_constants.ENHANCED_LEVEL:
            ask_skipping_validator = True
            skip_validator = False
            # Create validator objects here, so we're only creating them once
            bv = BasicValidator(parser)
            ev = EnhancedValidator()
            local_bv_objects = [bv(parser) for bv in LOCAL_BASIC_VALIDATORS]
            local_ev_objects = [ev() for ev in LOCAL_ENHANCED_VALIDATORS]
            print(f"Running enhanced validation for {parser}")
            for objects in self.measurements[parser].values():
                # Run the basic validators (standard one, plus configured local ones)
                prev_object_dict = dict()
                for curr_object in tqdm(objects):
                    if not bv.validate(curr_object, errors):
                        failed_validators.append(bv.name)
                    for local_bv in local_bv_objects:
                        if not local_bv.validate(curr_object, errors):
                            failed_validators.append(bv.name)
                    prev_object = None
                    if curr_object.platform_name in prev_object_dict:
                        prev_object = prev_object_dict[curr_object.platform_name]

                    # Run the enhanced validators (standard one, plus configured local ones)
                    if not skip_validator:
                        if not ev.validate(curr_object, errors, parser, prev_object):
                            failed_validators.append(ev.name)
                            if ask_skipping_validator:
                                (
                                    ask_skipping_validator,
                                    skip_validator,
                                    delete,
                                ) = self._ask_user_what_they_want(
                                    errors[-1], ask_skipping_validator, skip_validator
                                )
                                if delete:
                                    del errors[-1]
                        for local_ev in local_ev_objects:
                            if not local_ev.validate(curr_object, errors, parser, prev_object):
                                failed_validators.append(ev.name)
                                if ask_skipping_validator:
                                    (
                                        ask_skipping_validator,
                                        skip_validator,
                                        delete,
                                    ) = self._ask_user_what_they_want(
                                        errors[-1],
                                        ask_skipping_validator,
                                        skip_validator,
                                    )
                                    if delete:
                                        del errors[-1]

                    prev_object_dict[curr_object.platform_name] = curr_object
            print("Enhanced validator errors")
            pprint(errors)
            if not errors:
                return (True, failed_validators)
            return (False, failed_validators)
        else:
            raise ValueError(f"Invalid Validation Level {validation_level}")

    def commit(self, data_store, change_id):
        # Since measurements are saved by their importer names, iterate over each key
        # and save its measurement objects.
        extraction_log = list()
        for parser in self.measurements:
            total_objects = 0
            print(f"Submitting measurements extracted by {parser}.")
            for platform, objects in self.measurements[parser].items():
                total_objects += len(objects)

                # Split the list of objects to submit to the database into chunks
                # of 1000 objects each and submit in those chunks
                # This is because bulk_save_objects has no progress bar, so to get
                # a proper progress bar for submitting we need to chunk them
                # (making it a bit less efficient, but giving the user more
                # insight into the process)
                for chunk_objects in tqdm(chunked_list(objects, size=1000)):
                    # Bulk save table objects; state, etc.
                    data_store.session.bulk_save_objects(chunk_objects, return_defaults=True)
                    # Log saved objects
                    data_store.session.bulk_insert_mappings(
                        data_store.db_classes.Log,
                        [
                            dict(
                                table=t.__tablename__,
                                id=inspect(t).identity[0],
                                change_id=change_id,
                            )
                            for t in chunk_objects
                        ],
                    )

            extraction_log.append(f"{total_objects} measurements extracted by {parser}.")

        # Loop through the dict linking measurement objects to lists of extraction tokens
        # and fill in more details on the extraction tokens, then join all the lists together
        # ready for insert into the database
        extraction_data = []
        for measurement_obj, tokens_data in self.measurement_object_to_tokens_list.items():
            if measurement_obj is None:
                continue
            for entry in tokens_data:
                entry_id = getattr(measurement_obj, get_primary_key_for_table(measurement_obj))
                entry["entry_id"] = entry_id
                entry["destination_table"] = measurement_obj.__table__.name
                entry["datafile_id"] = self.datafile_id
            extraction_data += tokens_data

        print("Submitting extraction data")
        for chunk_extraction_data in tqdm(chunked_list(extraction_data, size=1000)):
            data_store.session.bulk_insert_mappings(
                data_store.db_classes.Extraction, chunk_extraction_data
            )

        self.measurement_object_to_tokens_list = {}
        self.pending_extracted_tokens = []

        return extraction_log


class LogMixin:
    @declared_attr
    def change(self):
        return relationship("Change", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def change_reason(self):
        return association_proxy("change", "reason")

    def __repr__(self):
        return f"Log(log_id={shorten_uuid(self.log_id)}, table={self.table}, id={shorten_uuid(self.id)}, change_id={shorten_uuid(self.change_id)})"


class TaggedItemMixin:
    _default_preview_fields = ["tag_name"]

    @declared_attr
    def tag(self):
        return relationship("Tag", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def tag_name(self):
        return association_proxy("tag", "name")

    @declared_attr
    def tagged_by(self):
        return relationship("User", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def tagged_by_name(self):
        return association_proxy("tagged_by", "name")


class StateMixin:
    _default_preview_fields = ["time", "sensor_name", "speed"]

    @declared_attr
    def sensor(self):
        return relationship("Sensor", lazy="joined", uselist=False)

    @declared_attr
    def sensor_name(self):
        return association_proxy("sensor", "name")

    @declared_attr
    def sensor_host(self):
        return association_proxy("sensor", "host")

    @declared_attr
    def platform_id(self):
        return association_proxy("sensor", "host")

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")

    @declared_attr
    def source(self):
        return relationship("Datafile", lazy="joined", uselist=False)

    @declared_attr
    def source_reference(self):
        return association_proxy("source", "reference")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    #
    # Speed properties
    #

    @hybrid_property
    def speed(self):
        # Return all speeds as metres per second
        if self._speed is None:
            return None
        else:
            return self._speed * (unit_registry.metre / unit_registry.second)

    @speed.setter
    def speed(self, speed):
        if speed is None:
            self._speed = None
            return

        # Check the given speed is a Quantity with a dimension of 'length / time'
        try:
            if not speed.check("[length]/[time]"):
                raise ValueError(
                    "Speed must be a Quantity with a dimensionality of [length]/[time]"
                )
        except AttributeError:
            raise TypeError("Speed must be a Quantity")

        # Set the actual speed attribute to the given value converted to metres per second
        self._speed = speed.to(unit_registry.metre / unit_registry.second).magnitude

    @speed.expression
    def speed(self):
        # We need a separate @speed.expression function to return a float rather than a
        # Quantity object, as otherwise this won't work in the SQLAlchemy filtering functions
        return self._speed

    #
    # Heading properties
    #

    @hybrid_property
    def heading(self):
        # Return all headings as degrees
        if self._heading is None:
            return None
        else:
            return (self._heading * unit_registry.radian).to(unit_registry.degree)

    @heading.setter
    def heading(self, heading):
        if heading is None:
            self._heading = None
            return

        # Check the given heading is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not heading.check(""):
                raise ValueError(
                    "Heading must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (heading.units == unit_registry.degree or heading.units == unit_registry.radian):
                raise ValueError("Heading must be a Quantity with angular units (degree or radian)")
        except AttributeError:
            raise TypeError("Heading must be a Quantity")

        # Set the actual heading attribute to the given value converted to radians
        self._heading = heading.to(unit_registry.radian).magnitude

    @heading.expression
    def heading(self):
        return self._heading

    #
    # Course properties
    #

    @hybrid_property
    def course(self):
        # Return all courses as degrees
        if self._course is None:
            return None
        else:
            return (self._course * unit_registry.radian).to(unit_registry.degree)

    @course.setter
    def course(self, course):
        if course is None:
            self._course = None
            return

        # Check the given course is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not course.check(""):
                raise ValueError(
                    "Course must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (course.units == unit_registry.degree or course.units == unit_registry.radian):
                raise ValueError("Course must be a Quantity with angular units (degree or radian)")
        except AttributeError:
            raise TypeError("Course must be a Quantity")

        # Set the actual course attribute to the given value converted to radians
        self._course = course.to(unit_registry.radian).magnitude

    @course.expression
    def course(self):
        return self._course


class ContactMixin:
    _default_preview_fields = ["time", "name", "bearing"]

    @declared_attr
    def sensor(self):
        return relationship("Sensor", lazy="joined", uselist=False)

    @declared_attr
    def sensor_name(self):
        return association_proxy("sensor", "name")

    @declared_attr
    def sensor_host(self):
        return association_proxy("sensor", "host")

    @declared_attr
    def platform_id(self):
        return association_proxy("sensor", "host")

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")

    @declared_attr
    def subject(self):
        return relationship("Platform", lazy="joined", uselist=False)

    @declared_attr
    def subject_name(self):
        return association_proxy("subject", "name")

    @declared_attr
    def source(self):
        return relationship("Datafile", lazy="joined", uselist=False)

    @declared_attr
    def source_reference(self):
        return association_proxy("source", "reference")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    #
    # Bearing properties
    #

    @hybrid_property
    def bearing(self):
        # Return all bearings as degrees
        if self._bearing is None:
            return None
        else:
            return (self._bearing * unit_registry.radian).to(unit_registry.degree)

    @bearing.setter
    def bearing(self, bearing):
        if bearing is None:
            self._bearing = None
            return

        # Check the given bearing is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not bearing.check(""):
                raise ValueError(
                    "Bearing must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (bearing.units == unit_registry.degree or bearing.units == unit_registry.radian):
                raise ValueError("Bearing must be a Quantity with angular units (degree or radian)")
        except AttributeError:
            raise TypeError("Bearing must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._bearing = bearing.to(unit_registry.radian).magnitude

    @bearing.expression
    def bearing(self):
        return self._bearing

    #
    # Rel Bearing properties
    #

    @hybrid_property
    def rel_bearing(self):
        # Return all rel_bearings as degrees
        if self._rel_bearing is None:
            return None
        else:
            return (self._rel_bearing * unit_registry.radian).to(unit_registry.degree)

    @rel_bearing.setter
    def rel_bearing(self, rel_bearing):
        if rel_bearing is None:
            self._rel_bearing = None
            return

        # Check the given bearing is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not rel_bearing.check(""):
                raise ValueError(
                    "Relative Bearing must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                rel_bearing.units == unit_registry.degree
                or rel_bearing.units == unit_registry.radian
            ):
                raise ValueError(
                    "Relative Bearing must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Relative Bearing must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._rel_bearing = rel_bearing.to(unit_registry.radian).magnitude

    @rel_bearing.expression
    def rel_bearing(self):
        return self._rel_bearing

    #
    # Ambig Bearing properties
    #

    @hybrid_property
    def ambig_bearing(self):
        # Return all ambig_bearings as degrees
        if self._ambig_bearing is None:
            return None
        else:
            return (self._ambig_bearing * unit_registry.radian).to(unit_registry.degree)

    @ambig_bearing.setter
    def ambig_bearing(self, ambig_bearing):
        if ambig_bearing is None:
            self._ambig_bearing = None
            return

        # Check the given bearing is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not ambig_bearing.check(""):
                raise ValueError(
                    "Ambig Bearing must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                ambig_bearing.units == unit_registry.degree
                or ambig_bearing.units == unit_registry.radian
            ):
                raise ValueError(
                    "Ambig Bearing must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Ambig Bearing must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._ambig_bearing = ambig_bearing.to(unit_registry.radian).magnitude

    @ambig_bearing.expression
    def ambig_bearing(self):
        return self._ambig_bearing

    #
    # MLA properties
    #

    @hybrid_property
    def mla(self):
        # Return all MLA's as degrees
        if self._mla is None:
            return None
        else:
            return (self._mla * unit_registry.radian).to(unit_registry.degree)

    @mla.setter
    def mla(self, mla):
        if mla is None:
            self._mla = None
            return

        # Check the given bearing is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not mla.check(""):
                raise ValueError("MLA must be a Quantity with a dimensionality of '' (ie. nothing)")
            if not (mla.units == unit_registry.degree or mla.units == unit_registry.radian):
                raise ValueError("MLA must be a Quantity with angular units (degree or radian)")
        except AttributeError:
            raise TypeError("MLA must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._mla = mla.to(unit_registry.radian).magnitude

    @mla.expression
    def mla(self):
        return self._mla

    #
    # SOA properties
    #

    @hybrid_property
    def soa(self):
        # Return all soas as metres per second
        if self._soa is None:
            return None
        else:
            return self._soa * (unit_registry.metre / unit_registry.second)

    @soa.setter
    def soa(self, soa):
        if soa is None:
            self._soa = None
            return

        # Check the given soa is a Quantity with a dimension of 'length / time'
        try:
            if not soa.check("[length]/[time]"):
                raise ValueError("SOA must be a Quantity with a dimensionality of [length]/[time]")
        except AttributeError:
            raise TypeError("SOA must be a Quantity")

        # Set the actual soa attribute to the given value converted to metres per second
        self._soa = soa.to(unit_registry.metre / unit_registry.second).magnitude

    @soa.expression
    def soa(self):
        return self._soa

    #
    # Orientation properties
    #

    @hybrid_property
    def orientation(self):
        # Return all orientation's as degrees
        if self._orientation is None:
            return None
        else:
            return (self._orientation * unit_registry.radian).to(unit_registry.degree)

    @orientation.setter
    def orientation(self, orientation):
        if orientation is None:
            self._orientation = None
            return

        # Check the given orientation is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not orientation.check(""):
                raise ValueError(
                    "Orientation must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                orientation.units == unit_registry.degree
                or orientation.units == unit_registry.radian
            ):
                raise ValueError(
                    "Orientation must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("Orientation must be a Quantity")

        # Set the actual bearing attribute to the given value converted to radians
        self._orientation = orientation.to(unit_registry.radian).magnitude

    @orientation.expression
    def orientation(self):
        return self._orientation

    #
    # Major property
    #

    @hybrid_property
    def major(self):
        # Return all majors as metres
        if self._major is None:
            return None
        else:
            return self._major * unit_registry.metre

    @major.setter
    def major(self, major):
        if major is None:
            self._major = None
            return

        # Check the given major is a Quantity with a dimension of 'length'
        try:
            if not major.check("[length]"):
                raise ValueError("Major must be a Quantity with a dimensionality of [length]")
        except AttributeError:
            raise TypeError("Major must be a Quantity")

        # Set the actual major attribute to the given value converted to metres
        self._major = major.to(unit_registry.metre).magnitude

    @major.expression
    def major(self):
        return self._major

    #
    # Minor property
    #

    @hybrid_property
    def minor(self):
        # Return all minors as metres
        if self._minor is None:
            return None
        else:
            return self._minor * unit_registry.metre

    @minor.setter
    def minor(self, minor):
        if minor is None:
            self._minor = None
            return

        # Check the given minor is a Quantity with a dimension of 'length'
        try:
            if not minor.check("[length]"):
                raise ValueError("Minor must be a Quantity with a dimensionality of [length]")
        except AttributeError:
            raise TypeError("Minor must be a Quantity")

        # Set the actual minor attribute to the given value converted to metres
        self._minor = minor.to(unit_registry.metre).magnitude

    @minor.expression
    def minor(self):
        return self._minor

    #
    # Range property
    #

    @hybrid_property
    def range(self):
        # Return all ranges as metres
        if self._range is None:
            return None
        else:
            return self._range * unit_registry.metre

    @range.setter
    def range(self, range):
        if range is None:
            self._range = None
            return

        # Check the given range is a Quantity with a dimension of 'length'
        try:
            if not range.check("[length]"):
                raise ValueError("Range must be a Quantity with a dimensionality of [length]")
        except AttributeError:
            raise TypeError("Range must be a Quantity")

        # Set the actual range attribute to the given value converted to metres
        self._range = range.to(unit_registry.metre).magnitude

    @range.expression
    def range(self):
        return self._range

    #
    # Freq property
    #

    @hybrid_property
    def freq(self):
        # Return all freqs as Hz
        if self._freq is None:
            return None
        else:
            return self._freq * unit_registry.hertz

    @freq.setter
    def freq(self, freq):
        if freq is None:
            self._freq = None
            return

        # Check the given freq is a Quantity with a dimension of 'time^-1' (ie. 'per unit time')
        try:
            if not freq.check("[time]^-1"):
                raise ValueError("Freq must be a Quantity with a dimensionality of [time]^-1")
        except AttributeError:
            raise TypeError("Freq must be a Quantity")

        # Set the actual freq attribute to the given value converted to hertz
        self._freq = freq.to(unit_registry.hertz).magnitude

    @freq.expression
    def freq(self):
        return self._freq


class LogsHoldingMixin:
    _default_preview_fields = ["time", "platform_name", "quantity"]

    @declared_attr
    def source(self):
        return relationship("Datafile", lazy="joined", uselist=False)

    @declared_attr
    def source_reference(self):
        return association_proxy("source", "reference")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    @declared_attr
    def platform(self):
        return relationship("Platform", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")

    @declared_attr
    def unit_type(self):
        return relationship("UnitType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def unit_type_name(self):
        return association_proxy("unit_type", "name")

    @declared_attr
    def commodity_type(self):
        return relationship("CommodityType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def commodity_type_name(self):
        return association_proxy("commodity_type", "name")


class CommentMixin:
    _default_preview_fields = ["time", "platform_name", "content"]

    @declared_attr
    def platform(self):
        return relationship("Platform", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")

    @declared_attr
    def platform_id(self):
        return association_proxy("platform", "platform_id")

    @declared_attr
    def comment_type(self):
        return relationship("CommentType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def comment_type_name(self):
        return association_proxy("comment_type", "name")

    @declared_attr
    def source(self):
        return relationship("Datafile", lazy="joined", uselist=False)

    @declared_attr
    def source_reference(self):
        return association_proxy("source", "reference")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")


class GeometryMixin:
    _default_preview_fields = ["name", "geo_type_name"]

    @hybrid_property
    def geometry(self):
        return self._geometry

    @geometry.setter
    def geometry(self, geom):
        if geom is None:
            self._geometry = None
            return

        # If we're given a Location object then convert it to WKT and set it
        # otherwise just pass through whatever we've been given
        if isinstance(geom, Location):
            self._geometry = geom.to_wkt()
        else:
            self._geometry = geom

    @geometry.expression
    def geometry(self):
        return self._geometry

    @declared_attr
    def serial(self):
        return relationship("Serial", lazy="joined", uselist=False)

    @declared_attr
    def subject_platform(self):
        return relationship(
            "Platform",
            lazy="joined",
            join_depth=1,
            uselist=False,
            foreign_keys="Geometry1.subject_platform_id",
        )

    # @declared_attr
    # def subject_platform_name(self):
    #     return association_proxy("subject_platform", "name")

    @declared_attr
    def sensor_platform(self):
        return relationship(
            "Platform",
            lazy="joined",
            join_depth=1,
            uselist=False,
            foreign_keys="Geometry1.sensor_platform_id",
        )

    # @declared_attr
    # def sensor_platform_name(self):
    #     return association_proxy("sensor_platform", "name")

    @declared_attr
    def geo_type(self):
        return relationship("GeometryType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def geo_type_name(self):
        return association_proxy("geo_type", "name")

    @declared_attr
    def geo_sub_type(self):
        return relationship("GeometrySubType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def geo_sub_type_name(self):
        return association_proxy("geo_sub_type", "name")

    @declared_attr
    def source(self):
        return relationship("Datafile", lazy="joined", uselist=False)

    # @declared_attr
    # def source_reference(self):
    #     return association_proxy("source", "reference")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")


class MediaMixin:
    _default_preview_fields = ["time", "platform_name", "sensor_name"]

    @declared_attr
    def media_type(self):
        return relationship("MediaType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def media_type_name(self):
        return association_proxy("media_type", "name")

    @declared_attr
    def sensor(self):
        return relationship("Sensor", lazy="joined", uselist=False)

    @declared_attr
    def sensor_name(self):
        return association_proxy("sensor", "name")

    @declared_attr
    def platform(self):
        return relationship(
            "Platform",
            foreign_keys="Media.platform_id",
        )

    @declared_attr
    def platform_name(self):
        return association_proxy("platform", "name")

    @declared_attr
    def subject(self):
        return relationship(
            "Platform",
            foreign_keys="Media.subject_id",
        )

    @declared_attr
    def subject_name(self):
        return association_proxy("subject", "name")

    @declared_attr
    def source(self):
        return relationship("Datafile", lazy="joined", uselist=False)

    # @declared_attr
    # def source_reference(self):
    #     return association_proxy("source", "reference")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")


class ElevationPropertyMixin:
    @hybrid_property
    def elevation(self):
        # Return all elevations as metres
        if self._elevation is None:
            return None
        else:
            return self._elevation * unit_registry.metre

    @elevation.setter
    def elevation(self, elevation):
        if elevation is None:
            self._elevation = None
            return

        # Check the given elevation is a Quantity with a dimension of 'length'
        try:
            if not elevation.check("[length]"):
                raise ValueError("Elevation must be a Quantity with a dimensionality of [length]")
        except AttributeError:
            raise TypeError("Elevation must be a Quantity")

        # Set the actual elevation attribute to the given value converted to metres
        self._elevation = elevation.to(unit_registry.metre).magnitude

    @elevation.expression
    def elevation(self):
        return self._elevation


class LocationPropertyMixin:
    @hybrid_property
    def location(self):
        if self._location is None:
            return None
        else:
            loc = Location()
            if isinstance(self._location, str):
                loc.set_from_wkt_string(self._location)
            else:
                loc.set_from_wkb(self._location.desc)

            return loc

    @location.setter
    def location(self, location):
        if location is None:
            self._location = None
            return

        if not isinstance(location, Location):
            raise TypeError("location value must be an instance of the Location class")

        if not location.check_valid():
            raise ValueError("location object does not have valid values")

        self._location = location.to_wkt()

    @location.expression
    def location(self):
        return self._location


class ActivationMixin:
    _default_preview_fields = ["name", "sensor_name", "start", "end"]

    @declared_attr
    def sensor(self):
        return relationship("Sensor", lazy="joined", uselist=False)

    @declared_attr
    def sensor_name(self):
        return association_proxy("sensor", "name")

    @declared_attr
    def source(self):
        return relationship("Datafile", lazy="joined", uselist=False)

    # @declared_attr
    # def source_reference(self):
    #     return association_proxy("source", "reference")

    @declared_attr
    def privacy(self):
        return relationship("Privacy", lazy="joined", uselist=False)

    @declared_attr
    def privacy_name(self):
        return association_proxy("privacy", "name")

    #
    # min_range property
    #
    @hybrid_property
    def min_range(self):
        # Return all min_ranges as metres
        if self._min_range is None:
            return None
        else:
            return self._min_range * unit_registry.metre

    @min_range.setter
    def min_range(self, min_range):
        if min_range is None:
            self._min_range = None
            return

        # Check the given min_range is a Quantity with a dimension of 'length'
        try:
            if not min_range.check("[length]"):
                raise ValueError("min_range must be a Quantity with a dimensionality of [length]")
        except AttributeError:
            raise TypeError("min_range must be a Quantity")

        # Set the actual min_range attribute to the given value converted to metres
        self._min_range = min_range.to(unit_registry.metre).magnitude

    @min_range.expression
    def min_range(self):
        return self._min_range

    #
    # max_range property
    #
    @hybrid_property
    def max_range(self):
        # Return all max_ranges as metres
        if self._max_range is None:
            return None
        else:
            return self._max_range * unit_registry.metre

    @max_range.setter
    def max_range(self, max_range):
        if max_range is None:
            self._max_range = None
            return

        # Check the given max_range is a Quantity with a dimension of 'length'
        try:
            if not max_range.check("[length]"):
                raise ValueError("max_range must be a Quantity with a dimensionality of [length]")
        except AttributeError:
            raise TypeError("max_range must be a Quantity")

        # Set the actual max_range attribute to the given value converted to metres
        self._max_range = max_range.to(unit_registry.metre).magnitude

    @max_range.expression
    def max_range(self):
        return self._max_range

    #
    # left_arc properties
    #

    @hybrid_property
    def left_arc(self):
        # Return all left_arcs as degrees
        if self._left_arc is None:
            return None
        else:
            return (self._left_arc * unit_registry.radian).to(unit_registry.degree)

    @left_arc.setter
    def left_arc(self, left_arc):
        if left_arc is None:
            self._left_arc = None
            return

        # Check the given left_arc is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not left_arc.check(""):
                raise ValueError(
                    "left_arc must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                left_arc.units == unit_registry.degree or left_arc.units == unit_registry.radian
            ):
                raise ValueError(
                    "left_arc must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("left_arc must be a Quantity")

        # Set the actual left_arc attribute to the given value converted to radians
        self._left_arc = left_arc.to(unit_registry.radian).magnitude

    @left_arc.expression
    def left_arc(self):
        return self._left_arc

    #
    # right_arc properties
    #

    @hybrid_property
    def right_arc(self):
        # Return all right_arcs as degrees
        if self._right_arc is None:
            return None
        else:
            return (self._right_arc * unit_registry.radian).to(unit_registry.degree)

    @right_arc.setter
    def right_arc(self, right_arc):
        if right_arc is None:
            self._right_arc = None
            return

        # Check the given right_arc is a Quantity with a dimension of '' and units of
        # degrees or radians
        try:
            if not right_arc.check(""):
                raise ValueError(
                    "right_arc must be a Quantity with a dimensionality of '' (ie. nothing)"
                )
            if not (
                right_arc.units == unit_registry.degree or right_arc.units == unit_registry.radian
            ):
                raise ValueError(
                    "right_arc must be a Quantity with angular units (degree or radian)"
                )
        except AttributeError:
            raise TypeError("right_arc must be a Quantity")

        # Set the actual right_arc attribute to the given value converted to radians
        self._right_arc = right_arc.to(unit_registry.radian).magnitude

    @right_arc.expression
    def right_arc(self):
        return self._right_arc


class ReferenceRepr:
    def __repr__(self):
        primary_key_col_name = get_primary_key_for_table(self)
        return (
            f"{self.__class__.__name__}(id={shorten_uuid(getattr(self, primary_key_col_name))} "
            f"name={self.name})"
        )


class SynonymMixin:
    def __repr__(self):
        return f"Synonym(id={shorten_uuid(self.synonym_id)}, table={self.table}, entity={shorten_uuid(self.entity)}, synonym={self.synonym})"


class ReferenceDefaultFields:
    _default_preview_fields = ["name"]
    _default_dropdown_fields = ["name"]


class GeometrySubTypeMixin:
    _default_preview_fields = ["name", "parent__name"]
    _default_dropdown_fields = ["name", "parent__name"]

    @declared_attr
    def parent_(self):
        return relationship("GeometryType", lazy="joined", innerjoin=True, uselist=False)

    @declared_attr
    def parent__name(self):
        return association_proxy("parent_", "name")


class NationalityMixin:
    _default_preview_fields = ["name", "priority"]
    _default_dropdown_fields = ["name"]
