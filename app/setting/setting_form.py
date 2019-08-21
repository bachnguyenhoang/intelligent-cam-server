from flask_wtf import FlaskForm
from wtforms import DecimalField, validators, FloatField, SubmitField
from opencv_server import Camera

class SettingForm(FlaskForm):
	#background subtractor
	background = DecimalField(label="Background ratio:", places=2, validators=[validators.InputRequired(),validators.NumberRange(0,1)])
	history = DecimalField(label="History:", places=0, default=Camera.subtractor_params['history'], validators=[validators.InputRequired(),validators.NumberRange(300, 700, message='error')])
	#feature parameters
	maxCorners = DecimalField(label="Max corners:", places=0, validators=[validators.InputRequired(),validators.NumberRange(min=0)])
	qualityLevel = DecimalField(label="Quality level:", places=3, validators=[validators.InputRequired(),validators.NumberRange(0, 1)])
	minDistance = DecimalField(label="Minimum distance:", places=0, validators=[validators.InputRequired(),validators.NumberRange(min=0)])
	blockSize = DecimalField(label="Block size:", places=0, validators=[validators.InputRequired(),validators.NumberRange(min=1)])
	#mask
	xmin = DecimalField(label="xmin:", places=0, validators=[validators.InputRequired(),validators.NumberRange(0, 639)])
	ymin = DecimalField(label="ymin:", places=0, validators=[validators.InputRequired(),validators.NumberRange(0, 479)])
	ymax = DecimalField(label="ymax:", places=0, validators=[validators.InputRequired(),validators.NumberRange(0, 479)])
	xmax = DecimalField(label="xmax:", places=0, validators=[validators.InputRequired(),validators.NumberRange(0, 639)])
	
	submit = SubmitField('Submit')
