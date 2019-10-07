import subprocess
import uuid
from pathlib import Path

import tempfile

from flask import jsonify, render_template, request
from flask_classful import route

from core.base.SuperManager import SuperManager
from core.interface.views.View import View


class SnipswatchView(View):

	def __init__(self):
		super().__init__()
		self._counter = 0
		self._thread = None
		self._file = Path(tempfile.gettempdir(), f'snipswatch_{uuid.uuid4()}')


	def index(self):
		return render_template('snipswatch.html', langData=self._langData)


	def startWatching(self, verbosity: int = 2):
		arg = ' -' + verbosity * 'v' if verbosity > 0 else ''
		process = subprocess.Popen(f'snips-watch {arg} --html', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		flag = SuperManager.getInstance().threadManager.newEvent('running')
		flag.set()
		while flag.isSet():
			out = process.stdout.readline().decode()
			if out:
				with open(self._file, 'a+') as fp:
					line = out.replace('<b><font color=#009900>', '<b><font color="green">').replace('#009900', '"yellow"').replace('#0000ff', '"green"')
					fp.write(line)


	def update(self):
		if not self._thread:
			self.refresh()

		return jsonify(data=self._getData())


	def refresh(self, verbosity: int = 2):
		if not self._thread or not self._thread.isAlive():
			self._thread = SuperManager.getInstance().threadManager.newThread(
				name='snipswatch',
				target=self.startWatching,
				autostart=True,
				args=[verbosity]
			)

		self._counter = 0
		return self.update()


	@route('/verbosity', methods=['POST'])
	def verbosity(self):
		if self._thread and self._thread.isAlive():
			self._thread.join(timeout=2)

		return self.refresh(verbosity=request.form.get('verbosity'))


	def _getData(self) -> list:
		try:
			data = self._file.open('r').readlines()
			ret = data[self._counter:]
			self._counter = len(data)
			return ret
		except:
			return list()
