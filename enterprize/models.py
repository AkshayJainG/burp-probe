from enterprize import db, bcrypt
from enterprize.services.burp import BurpProApi
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
import binascii
import uuid

# https://github.com/pallets-eco/flask-sqlalchemy/issues/1140

def get_current_utc_time():
    return datetime.now(timezone.utc)

def get_local_from_utc(dtg):
    return dtg.replace(tzinfo=timezone.utc).astimezone(tz=None)

def get_guid():
    return str(uuid.uuid4())


class BaseModel(db.Model):
    __abstract__ = True
    id: Mapped[str] = mapped_column(db.String(36), primary_key=True, default=get_guid)
    created: Mapped[str] = mapped_column(db.DateTime, nullable=False, default=get_current_utc_time)

    @property
    def created_as_string(self):
        return get_local_from_utc(self.created).strftime("%Y-%m-%d %H:%M:%S")


class User(BaseModel):
    __tablename__ = 'users'
    email: Mapped[str] = mapped_column(db.String(), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(db.String(), nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(), nullable=False)
    type: Mapped[str] = mapped_column(db.String(), nullable=False)
    #items: Mapped[list['Item']] = relationship('Item', back_populates='user', foreign_keys='Item.user_id', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password: write-only field')

    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(binascii.hexlify(password.encode()))

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, binascii.hexlify(password.encode()))

    def __repr__(self):
        return f"<User '{self.email}'>"


assets_scans = db.Table(
  'assets_scans',
  db.Column('asset_id', db.String(36), db.ForeignKey('assets.id')),
  db.Column('scan_id', db.String(36), db.ForeignKey('scans.id'))
)


class Asset(BaseModel):
    __tablename__ = 'assets'
    url: Mapped[str] = mapped_column(db.String(), nullable=False)
    description: Mapped[str] = mapped_column(db.String(), nullable=False)
    scans = relationship('Scan', secondary=assets_scans, back_populates='assets')

    def __repr__(self):
        return f"<Asset '{self.url}'>"


class Scan(BaseModel):
    __tablename__ = 'scans'
    description: Mapped[str] = mapped_column(db.String(), nullable=False)
    # from Form input
    configuration: Mapped[str] = mapped_column(db.String(), nullable=False) # JSON config stored as string
    # from JSON response
    audit_requests_made: Mapped[int] = mapped_column(db.Integer(), nullable=False)
    crawl_and_audit_caption: Mapped[str] = mapped_column(db.String(), nullable=False)
    crawl_and_audit_progress: Mapped[int] = mapped_column(db.Integer(), nullable=False)
    crawl_requests_made: Mapped[int] = mapped_column(db.Integer(), nullable=False)
    issue_events: Mapped[int] = mapped_column(db.Integer(), nullable=False)
    total_elapsed_time: Mapped[int] = mapped_column(db.Integer(), nullable=False)
    scan_status: Mapped[str] = mapped_column(db.String(), nullable=False)
    task_id: Mapped[str] = mapped_column(db.String(), nullable=False)
    node_id: Mapped[str] = mapped_column(db.String(36), db.ForeignKey('nodes.id'), nullable=False)
    node: Mapped['Node'] = relationship('Node', back_populates='scans', foreign_keys=[node_id])
    assets = relationship('Asset', secondary=assets_scans, back_populates='scans')

    @staticmethod
    def get_by_node_and_task(node_id, task_id):
        return Node.query.filter_by(node_id=node_id, task_id=task_id).first()

    def __repr__(self):
        return f"<Scan '{self.description}'>"


class Node(BaseModel):
    __tablename__ = 'nodes'
    description: Mapped[str] = mapped_column(db.String(), nullable=False)
    protocol: Mapped[str] = mapped_column(db.String(), nullable=False)
    hostname: Mapped[str] = mapped_column(db.String(), nullable=False)
    port: Mapped[str] = mapped_column(db.String(), nullable=False)
    api_key: Mapped[str] = mapped_column(db.String(), nullable=True)
    scans: Mapped[list['Scan']] = relationship('Scan', back_populates='node', foreign_keys='Scan.node_id', lazy='dynamic')

    @property
    def has_key(self):
        if self.api_key:
            return True
        return False

    @property
    def url(self):
        burp = BurpProApi(
            protocol=self.protocol,
            hostname=self.hostname,
            port=self.port,
            api_key=self.api_key,
        )
        return burp.url

    @property
    def is_alive(self):
        burp = BurpProApi(
            protocol=self.protocol,
            hostname=self.hostname,
            port=self.port,
            api_key=self.api_key,
        )
        return burp.is_alive()

    def __repr__(self):
        return f"<Node '{self.url}'>"
