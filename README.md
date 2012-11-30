ReDBox Researcher Portal
========================

Additions to the standard ReDBox portal that allows Researcher users to self-submit Collection metadata records.
The fields available to Researchers are based on requirements analysis done at UoA and are a subset of the fields available to Library staff users.

[ANDS-funded development done as part of the Metadata Stores project.]

This project may be run in stand-alone mode (for testing purposes). Use the usual ReDBox project commands to do this, i.e.

Build the project:

	#> mvn -Pbuild-package install

This will create the ReDBox run directories in $PROJECT_HOME.

Next, run the project in the usual way:

	#> $PROJECT_HOME/server/tf.sh start

This project may also be used as a library that can be used in an institutional build via a maven dependency.

To create a release of the redbox-researcher-portal library (this creates a zip file):

	#> mvn release:prepare

The build artefact (library file) should then be hosted by an appropriate maven repository. The artefact file can be found in: $PROJECT_HOME/redbox/target/redbox-researcher-portal-${version}-redbox-config.zip


To include the Researcher Portal library in your ReDBox institutional build,
add the following dependency to your pom.xml:

		<dependency>
			<groupId>au.edu.adelaide.redbox-mint</groupId>
			<artifactId>redbox-researcher-portal</artifactId>
			<classifier>redbox-config</classifier>
			<type>zip</type>
			<version>${researchersubmission.plugin.version}</version>
		</dependency>

You will need to add the unpack-researcher-portal execution to the maven-dependency-plugin:

		<!-- 1st - Unpack Generic ReDBox setup -->
		<plugin>
			<artifactId>maven-dependency-plugin</artifactId>
			<version>2.1</version>
			<executions>
				<execution>
		.
		.
		.
				</execution>

				<!-- Researcher Submission Portal resources -->
				<execution>
                        		<id>unpack-researcher-portal</id>
                        		<phase>generate-resources</phase>
                        		<goals>
						<goal>unpack</goal>
                        		</goals>
                        		<configuration>
						<outputDirectory>${project.home}</outputDirectory>
						<artifactItems>
							<artifactItem>
								<groupId>au.edu.adelaide.redbox-mint</groupId>
								<artifactId>redbox-researcher-portal</artifactId>
								<classifier>redbox-config</classifier>
								<type>zip</type>
							</artifactItem>
						</artifactItems>
					</configuration>
				</execution>
		.
		.
		.
			</executions>
		</plugin>

