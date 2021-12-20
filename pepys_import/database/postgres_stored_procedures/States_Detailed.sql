--Drop "States_Detailed" table
DROP TABLE IF EXISTS pepys."States_Detailed";

--Create "States_Detailed" table
CREATE TABLE pepys."States_Detailed" (
	state_id uuid primary key references pepys."States"(state_id),
	north double precision,
	east double precision,
	down double precision,
	x double precision,
	y double precision,
	z double precision,
	phi double precision,
	theta double precision,
	psi double precision,
	north_dot double precision,
	east_dot double precision,
	down_dot double precision,
	x_dot double precision,
	y_dot double precision,
	z_dot double precision,
	phi_dot double precision,
	theta_dot double precision,
	psi_dot double precision,
	north_dot_dot double precision,
	east_dot_dot double precision,
	down_dot_dot double precision,
	x_dot_dot double precision,
	y_dot_dot double precision,
	z_dot_dot double precision,
	phi_dot_dot double precision,
	theta_dot_dot double precision,
	psi_dot_dot double precision);

