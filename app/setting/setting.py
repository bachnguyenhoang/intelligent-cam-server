from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for, Response
)
from werkzeug.exceptions import abort
from app.setting import bp
from opencv_server import Camera
from app.setting.setting_form import SettingForm

@bp.route("/setting", methods=('GET', 'POST'))
def setting():
	form = SettingForm()
	if form.is_submitted():
		print("submitted")
	if form.validate():
		print("valid")
	print(form.errors)
	default = {**Camera.feature_params, **Camera.subtractor_params, **Camera.region_params}
	if form.validate_on_submit():
		Camera.set_feature_params(form.maxCorners.data, form.qualityLevel.data,form.minDistance.data,form.blockSize.data)
		Camera.set_subtractor_params(form.background.data,form.history.data)
		Camera.set_region_params(form.xmin.data,form.ymin.data,form.xmax.data,form.ymax.data)
		return redirect(url_for('home.index'))
	if request.method=='POST':
		if request.form['setting_buttons'] == 'Back':
			print('nothing changed')
			return redirect(url_for('home.index'))
	return render_template("setting/setting.html",form=form, default=default)

