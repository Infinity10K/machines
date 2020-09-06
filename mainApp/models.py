from django.db import models

class Worker(models.Model):
	name = models.CharField(max_length=50, null=False)
	position = models.CharField(max_length=50, null=True)
	qualification = models.IntegerField(null=True)
	#date_created = models.DateTimeField(auto_now_add=True, null=True)

	def __str__(self):
		return self.name

class Machine(models.Model):
	id = models.IntegerField(primary_key=True, serialize=False)
	model = models.CharField(max_length=50, null=True)
	age = models.IntegerField(null=True)

	def __int__(self):
		return self.id

class Task(models.Model):
	STATUS = (
			('В очереди', 'В очереди'),
			('Выполняется', 'Выполняется'),
			('Выполнено', 'Выполнено'),
			)

	worker = models.ManyToManyField(Worker)
	machine = models.ForeignKey(Machine, null=True, on_delete= models.SET_NULL)
	date_created = models.DateTimeField(auto_now_add=True, null=True)
	status = models.CharField(max_length=11, null=True, choices=STATUS)

	def __int__(self):
		return self.machine.id

class Telemetry(models.Model):
	date_created = models.DateTimeField(auto_now_add=True, null=True)
	machine = models.ForeignKey(Machine, null=True, on_delete=models.SET_NULL)
	volt = models.FloatField(null=True)
	rotate = models.FloatField(null=True)
	pressure = models.FloatField(null=True)
	vibration = models.FloatField(null=True)

class Replacement(models.Model):
	date_created = models.DateTimeField(auto_now_add=True, null=True)
	machine = models.ForeignKey(Machine, null=True, on_delete=models.SET_NULL)
	compID = models.CharField(max_length=10, null=True)

	def __str__(self):
		return self.compID

class Failure(models.Model):
	date_created = models.DateTimeField(auto_now_add=True, null=True)
	machine = models.ForeignKey(Machine, null=True, on_delete=models.SET_NULL)
	failure = models.CharField(max_length=50, null=True)

	def __str__(self):
		return self.failure

class Error(models.Model):
	date_created = models.DateTimeField(auto_now_add=True, null=True)
	machine = models.ForeignKey(Machine, null=True, on_delete=models.SET_NULL)
	error = models.CharField(max_length=50, null=True)

	def __str__(self):
		return self.error