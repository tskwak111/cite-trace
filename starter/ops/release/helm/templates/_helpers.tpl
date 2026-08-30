{{/*
  CiteTrace Helm helpers.
*/}}
{{- define "citetrace.name" -}}
{{- .Chart.Name | default "citetrace" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "citetrace.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := include "citetrace.name" . }}
{{- if .Values.fullnameSuffix }}
{{- printf "%s-%s" $name .Values.fullnameSuffix | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "citetrace.labels" -}}
{{- include "citetrace.selectorLabels" . | nindent 0 }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
app.kubernetes.io/part-of: {{ include "citetrace.name" . | quote }}
{{- end }}

{{- define "citetrace.selectorLabels" -}}
app.kubernetes.io/name: {{ include "citetrace.name" . | quote }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
{{- end }}
